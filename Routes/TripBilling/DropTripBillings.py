from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, time

from Models import db
from Models.Route.Routing.DropRoutingWithAllEmployess import DropRouting
from Models.TripBilling.DropTripBillings import DropTripBilling
from Models.TripBilling.BillingPolicies import BillingPolicy
from Models.TripBilling.DropTripEmployeeLink import DropTripEmployeeLink
from Models.Vechile.VechileDetails import VechileDetails
from Routes import home
from decimal import Decimal
from geopy.distance import geodesic
from sqlalchemy.exc import IntegrityError


def calculate_fare_and_create_bill_for_drop(vehicle_id, schedule_id):
    # Step 0: Prevent duplicate billing
    existing = DropTripBilling.query.filter_by(vehicle_id=vehicle_id, schedule_id=schedule_id).first()
    if existing:
        print(f"⚠️ Billing already exists (ID: {existing.id}) for vehicle_id={vehicle_id}, schedule_id={schedule_id}")
        return existing

    # Step 1: Load routing entries
    trip_entries = DropRouting.query.filter_by(vehicle_id=vehicle_id, schedule_id=schedule_id).all()
    if not trip_entries:
        raise ValueError(f"No routing data found for vehicle_id={vehicle_id}, schedule_id={schedule_id}")

    # Step 2: Load vehicle and billing policy
    vehicle = VechileDetails.query.get(vehicle_id)
    if not vehicle:
        raise ValueError(f"Vehicle not found for ID {vehicle_id}")
    billing_policy = vehicle.billing_policy
    if not billing_policy:
        raise ValueError(f"Billing policy missing for vehicle ID {vehicle_id}")

    # Step 3: Normalize billing mode
    mode_map = {
        'zone-based billing': 'zonebased',
        'distance-based pricing': 'distancebased',
        'subscription-based billing': 'subscription',
        'time + distance pricing': 'time_distance',
    }
    billing_mode_raw = billing_policy.billing_mode.lower().strip()
    billing_mode = mode_map.get(billing_mode_raw)
    if not billing_mode:
        raise ValueError(f"Unsupported billing mode: {billing_policy.billing_mode}")

    # Step 4: Get trip info
    route_name = trip_entries[0].route_name or "Unknown"
    total_distance = float(trip_entries[0].route_distance or 0.0)
    fare = 0.0

    # Step 5: Fare calculation
    if billing_mode == 'zonebased':
        zone = next((z for z in billing_policy.zones if z.distance_min <= total_distance <= z.distance_max), None)
        if not zone:
            raise ValueError(f"No zone found for distance {total_distance} km")
        fare = zone.fixed_price
    elif billing_mode == 'distancebased':
        fare = billing_policy.base_fare + (total_distance * billing_policy.rate_per_km)
    elif billing_mode == 'subscription':
        fare = billing_policy.extra_ride_price
    elif billing_mode == 'time_distance':
        raise NotImplementedError("Time + Distance billing not implemented.")

    print(f"💰 Calculated fare: ₹{fare:.2f} | Mode: {billing_mode} | Distance: {total_distance:.2f} km")

    # Step 6: Create DropTripBilling record
    trip_bill = DropTripBilling(
        vehicle_id=vehicle_id,
        schedule_id=schedule_id,
        billing_policy_id=billing_policy.id,
        trip_date=datetime.utcnow(),
        distance_travelled=round(total_distance, 2),
        fare_amount=round(Decimal(fare), 2),
        billing_mode=billing_mode,
        status='unpaid',
        route_name=route_name
    )
    db.session.add(trip_bill)

    try:
        db.session.flush()
        print(f"🧾 Billing record flushed with ID: {trip_bill.id}")
    except IntegrityError as e:
        db.session.rollback()
        raise ValueError(f"Flush failed: {str(e)}")

    # Step 7: Create employee links
    links = []
    for entry in trip_entries:
        if entry.employee_id:
            link = DropTripEmployeeLink(
                drop_trip_billing_id=trip_bill.id,
                employee_id=entry.employee_id,
                drop_routing_id=entry.id
            )
            links.append(link)

    if links:
        db.session.add_all(links)
    else:
        print("⚠️ No employee links found for drop trip.")

    # Step 8: Final commit
    try:
        db.session.commit()
        print(f"✅ Drop trip bill committed (ID: {trip_bill.id}) with {len(links)} employee entries.")
    except IntegrityError as e:
        db.session.rollback()
        raise ValueError(f"Commit failed: {str(e)}")

    return trip_bill




# def calculate_fare_and_create_bill_for_drop(vehicle_id, schedule_id):
#     trip_entries = DropRouting.query.filter_by(
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
#     # ✅ Get route_name and route_distance from first trip entry
#     route_name = trip_entries[0].route_name if trip_entries[0].route_name else "Unknown Route"
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
#     # --- Step 3: Create TripBilling record ---
#     trip_bill = DropTripBilling(
#         vehicle_id=vehicle_id,
#         billing_policy_id=billing_policy.id,
#         trip_date=datetime.utcnow(),
#         distance_travelled=round(total_distance, 2),  # ✅ using route_distance
#         fare_amount=round(Decimal(fare), 2),
#         billing_mode=billing_mode,
#         status='unpaid',
#         route_name=route_name  # ✅ use the route name from the routing
#     )
#     db.session.add(trip_bill)
#     db.session.flush()
#
#     trip_employee_links = []
#     for entry in trip_entries:
#         if entry.employee_id:
#             link = DropTripEmployeeLink(
#                 drop_trip_billing_id=trip_bill.id,
#                 employee_id=entry.employee_id,
#                 drop_routing_id=entry.id
#             )
#             trip_employee_links.append(link)
#
#     db.session.add_all(trip_employee_links)
#
#     try:
#         db.session.commit()
#         print(f"✅ Trip bill created for vehicle ID {vehicle_id} with {len(trip_entries)} employee entries.")
#     except IntegrityError as e:
#         db.session.rollback()
#         raise ValueError(f"Database error occurred: {str(e)}")
#
#     return trip_bill
