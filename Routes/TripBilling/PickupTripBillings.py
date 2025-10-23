from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, time

from Models import db
from Models.Route.Routing.PickupRoutingWithAllEmployees import PickupRouting
from Models.TripBilling.PickupTripBillings import PickupTripBilling
from Models.TripBilling.BillingPolicies import BillingPolicy
from Models.TripBilling.PickupTripEmployeeLink import PickupTripEmployeeLink
from Models.Vechile.VechileDetails import VechileDetails
from Routes import home
from decimal import Decimal
from geopy.distance import geodesic
from sqlalchemy.exc import IntegrityError




def calculate_fare_and_create_bill_for_pickup(vehicle_id, schedule_id):
    # Step 0: Avoid duplicate bills
    existing = PickupTripBilling.query.filter_by(
        vehicle_id=vehicle_id, schedule_id=schedule_id
    ).first()
    if existing:
        print(f"⚠️ Existing billing found (ID {existing.id}), not creating duplicate.")
        return existing

    # Step 1: Get routing entries
    trip_entries = PickupRouting.query.filter_by(
        vehicle_id=vehicle_id, schedule_id=schedule_id
    ).all()
    if not trip_entries:
        raise ValueError(f"No routing entries for vehicle={vehicle_id}, schedule={schedule_id}")

    # Step 2: Fetch vehicle and policy
    vehicle = VechileDetails.query.get(vehicle_id)
    if not vehicle:
        raise ValueError("Vehicle not found")

    policy = vehicle.billing_policy
    if not policy:
        raise ValueError("Missing billing policy")

    # Step 3: Determine billing mode
    mode_map = {
        'zone-based billing': 'zonebased',
        'distance-based pricing': 'distancebased',
        'subscription-based billing': 'subscription',
        'time + distance pricing': 'time_distance',
    }
    billing_mode = mode_map.get(policy.billing_mode.lower().strip())
    if not billing_mode:
        raise ValueError(f"Unsupported billing mode: {policy.billing_mode}")

    # Step 4: Calculate distance and fare
    total_distance = float(trip_entries[0].route_distance or 0.0)
    if billing_mode == 'zonebased':
        zone = next((z for z in policy.zones if z.distance_min <= total_distance <= z.distance_max), None)
        if not zone:
            raise ValueError(f"No zone for distance {total_distance} km")
        fare = zone.fixed_price
    elif billing_mode == 'distancebased':
        fare = policy.base_fare + total_distance * policy.rate_per_km
    elif billing_mode == 'subscription':
        fare = policy.extra_ride_price
    else:
        raise NotImplementedError("Time + distance billing not supported yet")

    print(f"Calculated fare ₹{fare:.2f} by {billing_mode} over {total_distance:.2f} km")

    # Step 5: Create billing entry
    trip_bill = PickupTripBilling(
        vehicle_id=vehicle_id,
        schedule_id=schedule_id,
        billing_policy_id=policy.id,
        trip_date=datetime.utcnow(),
        distance_travelled=round(total_distance, 2),
        fare_amount=round(Decimal(fare), 2),
        billing_mode=billing_mode,
        status='unpaid',
        route_name=trip_entries[0].route_name or "UnknownRoute"
    )
    db.session.add(trip_bill)

    try:
        db.session.flush()
        print(f"Flushed billing ID: {trip_bill.id}")
    except IntegrityError as e:
        db.session.rollback()
        raise ValueError(f"Flush error: {e}")

    # Step 6: Link employees
    links = []
    for entry in trip_entries:
        if entry.employee_id:
            links.append(PickupTripEmployeeLink(
                pickup_trip_billing_id=trip_bill.id,
                employee_id=entry.employee_id,
                pickup_routing_id=entry.id
            ))

    if links:
        db.session.add_all(links)
    else:
        print("⚠️ No employee links to insert")

    # Step 7: Commit and Handle Errors
    try:
        db.session.commit()
        print(f"✅ Billing record created (ID {trip_bill.id}) with {len(links)} employee links")
    except IntegrityError as e:
        db.session.rollback()
        raise ValueError(f"Commit failed: {e}")

    return trip_bill






# def calculate_fare_and_create_bill_for_pickup(vehicle_id, schedule_id):
#     trip_entries = PickupRouting.query.filter_by(
#         vehicle_id=vehicle_id,
#         schedule_id=schedule_id
#     ).all()
#
#     if not trip_entries:
#         raise ValueError(f"No trip routing data found for vehicle_id={vehicle_id} and schedule_id={schedule_id}.")
#
#     vehicle = VechileDetails.query.get(vehicle_id)
#     if not vehicle:
#         raise ValueError(f"Vehicle not found for vehicle_id={vehicle_id}.")
#
#     billing_policy = vehicle.billing_policy
#     if not billing_policy:
#         raise ValueError(f"Billing policy not found for vehicle ID {vehicle_id}. Ensure billing_policy_id is valid.")
#
#     # Normalize billing mode
#     billing_mode_raw = billing_policy.billing_mode.lower().strip()
#     mode_map = {
#         'zone-based billing': 'zonebased',
#         'distance-based pricing': 'distancebased',
#         'subscription-based billing': 'subscription',
#         'time + distance pricing': 'time_distance',
#     }
#     billing_mode = mode_map.get(billing_mode_raw)
#
#     if not billing_mode:
#         raise ValueError(f"Unsupported billing mode '{billing_policy.billing_mode}'.")
#
#     # ✅ Use route_distance from the first entry
#     route_name = trip_entries[0].route_name if trip_entries[0].route_name else "UnknownRoute"
#     route_distance = trip_entries[0].route_distance if trip_entries[0].route_distance else 0.0
#     total_distance = float(route_distance)
#
#     # --- Step 2: Calculate fare based on billing mode ---
#     fare = 0.0
#     if billing_mode == 'zonebased':
#         matched_zone = next((z for z in billing_policy.zones if z.distance_min <= total_distance <= z.distance_max), None)
#         if not matched_zone:
#             raise ValueError(f"No matching zone for distance {total_distance:.2f} km under billing policy ID {billing_policy.id}")
#         fare = matched_zone.fixed_price
#
#     elif billing_mode == 'distancebased':
#         fare = billing_policy.base_fare + (total_distance * billing_policy.rate_per_km)
#
#     elif billing_mode == 'subscription':
#         fare = billing_policy.extra_ride_price
#
#     elif billing_mode == 'time_distance':
#         raise NotImplementedError("Time + Distance billing not yet implemented.")
#
#     # --- Step 3: Create a single PickupTripBilling record ---
#     trip_bill = PickupTripBilling(
#         vehicle_id=vehicle_id,
#         billing_policy_id=billing_policy.id,
#         trip_date=datetime.utcnow(),
#         distance_travelled=round(total_distance, 2),  # ✅ storing route_distance here
#         fare_amount=round(Decimal(fare), 2),
#         billing_mode=billing_mode,
#         status='unpaid',
#         route_name=route_name
#     )
#     db.session.add(trip_bill)
#     db.session.flush()
#
#     # --- Step 4: Link employees to the billing record ---
#     trip_employee_links = []
#     for entry in trip_entries:
#         if entry.employee_id:
#             link = PickupTripEmployeeLink(
#                 pickup_trip_billing_id=trip_bill.id,
#                 employee_id=entry.employee_id,
#                 pickup_routing_id=entry.id
#             )
#             trip_employee_links.append(link)
#
#     db.session.add_all(trip_employee_links)
#
#     try:
#         db.session.commit()
#         print(f"✅ Pickup trip bill created for vehicle ID {vehicle_id} with {len(trip_entries)} employee entries.")
#     except IntegrityError as e:
#         db.session.rollback()
#         raise ValueError(f"Database error occurred: {str(e)}")
#
#     return trip_bill












# @home.route('/vehicle_billing_summary')
# def vehicle_billing_summary():
#     results = db.session.query(
#         VehicleDetails.vehicle_number,
#         VehicleDetails.vehicle_type,
#         db.func.sum(TripBilling.fare).label('total_earned')
#     ).join(TripBilling).group_by(
#         VehicleDetails.vehicle_number, VehicleDetails.vehicle_type
#     ).all()#
#     return jsonify([
#         {'vehicle_number': r.vehicle_number, 'vehicle_type': r.vehicle_type, 'total_earned': r.total_earned}
#         for r in results
#     ])







