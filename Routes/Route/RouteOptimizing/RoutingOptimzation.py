import json
import requests
import random
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from Models import db
from Models.Employee.Employees import Employees
from Models.Schedules.Employee_schedules import Employees_schedules
from Models.Vechile.VechileDetails import VechileDetails
from Models.Route.Routing.PickupRoutingWithAllEmployees import PickupRouting
from Models.Route.Routing.DropRoutingWithAllEmployess import DropRouting
import os
import openrouteservice
from geopy.distance import geodesic
from datetime import datetime
from Routes import home

# source_coordinates = [17.441640, 78.381263]  # Office coordinates
#
#
# def calculate_distance(origin, destination):
#     return geodesic(origin, destination).km
#
#
# def get_pickup_vehicle(vehicle_details):
#     vehicle = VechileDetails.query.filter_by(vechile_number=vehicle_details.get('vechile_number')).first()
#     if not vehicle:
#         vehicle = VechileDetails(
#             vendor_type=vehicle_details.get('vendor_type'),
#             vendor_name=vehicle_details.get('vendor_name'),
#             vechile_owner_name=vehicle_details.get('vechile_owner_name'),
#             vechile_driver_name=vehicle_details.get('vechile_driver_name'),
#             vechile_name=vehicle_details.get('vechile_name'),
#             vechile_model=vehicle_details.get('vechile_model'),
#             vechile_number=vehicle_details.get('vechile_number'),
#             vechile_owner_mobile_no=vehicle_details.get('vechile_owner_mobile_no'),
#             vechile_driver_mobile_no=vehicle_details.get('vechile_driver_mobile_no')
#         )
#         db.session.add(vehicle)
#         db.session.commit()
#     return vehicle
#
#
# def insert_pickup_employee(employee_data):
#     employee = Employees.query.filter_by(employee_id=employee_data['employee_id']).first()
#     if not employee:
#         employee = Employees(
#             employee_id=employee_data['employee_id'],
#             employee_name=employee_data['employee_name'],
#             employee_address=employee_data['employee_address'],
#             latitude=employee_data['employee_coordinates'][0],
#             longitude=employee_data['employee_coordinates'][1],
#             gender='N/A',
#             employee_mobile_no=0,
#             employee_email='N/A',
#             process='N/A',
#             password='N/A',
#             role='N/A',
#             poc_name='N/A',
#             poc_mobile_no=0
#         )
#         db.session.add(employee)
#         db.session.commit()
#     return employee
#
#
# def insert_pickup_schedule(employee, schedule_data):
#     shift_date = datetime.strptime(schedule_data['shift_date'], '%Y-%m-%d').date()
#     schedule = Employees_schedules.query.filter_by(
#         employee_id=employee.employee_id,
#         shift_date=shift_date
#     ).first()
#
#     if not schedule:
#         schedule = Employees_schedules(
#             employee_id=employee.employee_id,
#             shift_date=shift_date,
#             pickup_time=datetime.strptime(schedule_data['pickup_time'], '%H:%M:%S').time() if schedule_data.get('pickup_time') else None,
#             drop_time=datetime.strptime(schedule_data['drop_time'], '%H:%M:%S').time() if schedule_data.get('drop_time') else None,
#             pickup_trip_status="Routing Done"
#         )
#         db.session.add(schedule)
#     else:
#         schedule.pickup_trip_status = "Routing Done"
#
#     db.session.commit()
#     return schedule
#
#
# def handle_pickup_routing(request_data):
#     if not request_data:
#         return jsonify({"error": "Empty request body."}), 400
#
#     shift_key = next(iter(request_data))
#     shift_data = request_data[shift_key]
#
#     try:
#         pickup_group_time = datetime.strptime(shift_key, "%H:%M:%S").time()
#     except ValueError:
#         pickup_group_time = datetime.strptime(shift_key, "%H:%M").time()
#
#     vehicle_details = None
#     vehicle = None
#     employee_with_distances = []
#     cumulative_distance = 0
#     last_coordinates = source_coordinates
#
#     for cluster_data in shift_data:
#         cluster_id = cluster_data.get("clusterId")
#         if not cluster_id:
#             continue
#
#         employee_list = cluster_data.get("employeeList", [])
#         if not employee_list:
#             continue
#
#         if not vehicle:
#             vehicle_details = cluster_data.get("vehicleDetails", {})
#             vehicle = get_pickup_vehicle(vehicle_details)
#
#         for idx, employee in enumerate(employee_list):
#             employee_coordinates = employee["employee_coordinates"]
#             distance = calculate_distance(last_coordinates, employee_coordinates)
#             cumulative_distance += distance
#             last_coordinates = employee_coordinates
#
#             employee_record = insert_pickup_employee(employee)
#             schedule = insert_pickup_schedule(employee_record, employee)
#
#             try:
#                 calculated_pickup_time = datetime.strptime(employee["calculated_pickup_time"], "%H:%M:%S").time()
#             except ValueError:
#                 return jsonify({
#                     "error": f"Invalid time format for calculated_pickup_time: {employee['calculated_pickup_time']}"
#                 }), 400
#
#             # ✅ Check for existing routing before insert
#             existing_routing = PickupRouting.query.filter_by(
#                 employee_id=employee_record.employee_id,
#                 schedule_id=schedule.schedule_id,
#                 vehicle_id=vehicle.id,
#                 pickup_timing_group=pickup_group_time,
#                 cluster_in_pickup_group=cluster_id
#             ).first()
#
#             if existing_routing:
#                 return jsonify({
#                     "error": f"Routing already exists for employee {employee_record.employee_id} "
#                              f"in cluster {cluster_id} at {pickup_group_time}."
#                 }), 400
#
#             routing = PickupRouting(
#                 employee_id=employee_record.employee_id,
#                 schedule_id=schedule.schedule_id,
#                 vehicle_id=vehicle.id,
#                 pickup_sequence=idx + 1,
#                 distance_from_last=round(distance, 2),
#                 cumulative_distance=round(cumulative_distance, 2),
#                 calculated_pickup_time=calculated_pickup_time,
#                 pickup_timing_group=pickup_group_time,
#                 cluster_in_pickup_group=cluster_id,
#                 pickup_vehicle_assigned_at=datetime.now(),
#                 on_board_OTP=random.randint(1000, 9999),
#                 off_board_OTP=random.randint(1000, 9999),
#             )
#             db.session.add(routing)
#
#             employee_with_distances.append({
#                 'employee_id': employee["employee_id"],
#                 'employee_name': employee["employee_name"],
#                 'employee_address': employee["employee_address"],
#                 'pickup_time': employee["pickup_time"],
#                 'drop_time': employee.get("drop_time"),
#                 'pickup_sequence': idx + 1,
#                 'distance_from_last': round(distance, 2),
#                 'cumulative_distance': round(cumulative_distance, 2),
#                 'pickup_trip_status': "Routing Done",
#                 'cluster': cluster_id
#             })
#
#     try:
#         db.session.commit()
#     except IntegrityError as e:
#         db.session.rollback()
#         return jsonify({"error": f"DB integrity error: {str(e)}"}), 400
#
#     return jsonify({
#         "route": employee_with_distances,
#         "total_distance": round(cumulative_distance, 2),
#         "vehicle_details": vehicle_details
#     }), 200
#
#
# @home.route('/get/pickup-routing', methods=['POST'])
# def get_pickup_routing():
#     request_data = request.get_json()
#     return handle_pickup_routing(request_data)


source_coordinates = [17.441640, 78.381263]  # Office coordinates


def calculate_distance(origin, destination):
    return geodesic(origin, destination).km


def get_pickup_vehicle(vehicle_details):
    vehicle = VechileDetails.query.filter_by(vechile_number=vehicle_details.get('vechile_number')).first()
    if not vehicle:
        vehicle = VechileDetails(
            vendor_type=vehicle_details.get('vendor_type'),
            vendor_name=vehicle_details.get('vendor_name'),
            vechile_owner_name=vehicle_details.get('vechile_owner_name'),
            vechile_driver_name=vehicle_details.get('vechile_driver_name'),
            vechile_name=vehicle_details.get('vechile_name'),
            vechile_model=vehicle_details.get('vechile_model'),
            vechile_number=vehicle_details.get('vechile_number'),
            vechile_owner_mobile_no=vehicle_details.get('vechile_owner_mobile_no'),
            vechile_driver_mobile_no=vehicle_details.get('vechile_driver_mobile_no')
        )
        db.session.add(vehicle)
        db.session.commit()
    return vehicle


def insert_pickup_employee(employee_data):
    employee = Employees.query.filter_by(employee_id=employee_data['employee_id']).first()
    if not employee:
        employee = Employees(
            employee_id=employee_data['employee_id'],
            employee_name=employee_data['employee_name'],
            employee_address=employee_data['employee_address'],
            latitude=employee_data['employee_coordinates'][0],
            longitude=employee_data['employee_coordinates'][1],
            gender='N/A',
            employee_mobile_no=0,
            employee_email='N/A',
            process='N/A',
            password='N/A',
            role='N/A',
            poc_name='N/A',
            poc_mobile_no=0
        )
        db.session.add(employee)
        db.session.commit()
    return employee


def insert_pickup_schedule(employee, schedule_data):
    shift_date = datetime.strptime(schedule_data['shift_date'], '%Y-%m-%d').date()
    schedule = Employees_schedules.query.filter_by(
        employee_id=employee.employee_id,
        shift_date=shift_date
    ).first()

    if not schedule:
        schedule = Employees_schedules(
            employee_id=employee.employee_id,
            shift_date=shift_date,
            pickup_time=datetime.strptime(schedule_data['pickup_time'], '%H:%M:%S').time() if schedule_data.get('pickup_time') else None,
            drop_time=datetime.strptime(schedule_data['drop_time'], '%H:%M:%S').time() if schedule_data.get('drop_time') else None,
            pickup_trip_status="Routing Done"
        )
        db.session.add(schedule)
    else:
        schedule.pickup_trip_status = "Routing Done"

    db.session.commit()
    return schedule

ORS_API_KEY = os.getenv('ORS_API_KEY', '5b3ce3597851110001cf6248b5bf2e59230248ed8975bc8a02758ae2')
ors_client = openrouteservice.Client(key=ORS_API_KEY)


def get_route_distance_km(origin, destination):
    try:
        # ORS expects coordinates in [lon, lat] format
        coords = [
            [origin[1], origin[0]],  # Convert [lat, lon] → [lon, lat]
            [destination[1], destination[0]]
        ]

        # Request directions from ORS API
        response = ors_client.directions(
            coordinates=coords,
            profile='driving-car',  # Try 'driving-car', 'cycling-regular', 'foot-walking'
            format='geojson',
            optimize_waypoints=False,
            validate=False
        )

        # Check if the response contains expected data
        if 'features' not in response or len(response['features']) == 0:
            raise ValueError("ORS API returned an empty response or no features found.")

        # Extract the first segment from the response
        segment = response['features'][0]['properties']['segments'][0]
        distance_meters = segment.get('distance', 0)

        if distance_meters == 0:
            raise ValueError("Distance in response is zero. Please check the coordinates or the route.")

        # Convert distance from meters to kilometers
        distance_km = round(distance_meters / 1000, 2)

        # Optional: Log the entire response for debugging purposes
        print("ORS Response:", response)

        return distance_km

    except Exception as e:
        print(f"Error in ORS API call: {e}")
        # Fallback: Use geodesic as a direct line measurement
        geodesic_distance = round(geodesic(origin, destination).km, 2)
        print(f"Using geodesic fallback distance: {geodesic_distance} km")
        return geodesic_distance


# Fallback to geodesic distance if ORS fails



def handle_pickup_routing(request_data):
    if not request_data:
        return jsonify({"error": "Empty request body."}), 400

    shift_key = next(iter(request_data))
    shift_data = request_data[shift_key]

    try:
        pickup_group_time = datetime.strptime(shift_key, "%H:%M:%S").time()
    except ValueError:
        pickup_group_time = datetime.strptime(shift_key, "%H:%M").time()

    vehicle_details = None
    vehicle = None
    employee_with_distances = []
    all_routings = []
    total_combined_distance = 0  # Sum for final response

    for cluster_data in shift_data:
        cluster_id = cluster_data.get("clusterId")
        route_name = cluster_data.get("routeName")

        if not cluster_id:
            continue

        employee_list = cluster_data.get("employeeList", [])
        if not employee_list:
            continue

        if not vehicle:
            vehicle_details = cluster_data.get("vehicleDetails", {})
            vehicle = get_pickup_vehicle(vehicle_details)

        cluster_routings = []
        employee_coordinates_chain = []  # For distance calculation
        cumulative_distance = 0
        last_coordinates = None

        for idx, employee in enumerate(employee_list):
            employee_coordinates = employee["employee_coordinates"]
            employee_coordinates_chain.append(employee_coordinates)

            if last_coordinates is None:
                distance = 0  # No distance for first employee
            else:
                distance = get_route_distance_km(last_coordinates, employee_coordinates)

            cumulative_distance += distance
            last_coordinates = employee_coordinates

            employee_record = insert_pickup_employee(employee)
            schedule = insert_pickup_schedule(employee_record, employee)

            try:
                calculated_pickup_time = datetime.strptime(employee["calculated_pickup_time"], "%H:%M:%S").time()
            except ValueError:
                return jsonify({
                    "error": f"Invalid time format for calculated_pickup_time: {employee['calculated_pickup_time']}."
                }), 400

            existing_routing = PickupRouting.query.filter_by(
                employee_id=employee_record.employee_id,
                schedule_id=schedule.schedule_id,
                vehicle_id=vehicle.id,
                pickup_timing_group=pickup_group_time,
                cluster_in_pickup_group=cluster_id
            ).first()

            if existing_routing:
                return jsonify({
                    "error": f"Routing already exists for employee {employee_record.employee_id} "
                             f"in cluster {cluster_id} at {pickup_group_time}."
                }), 400

            routing = PickupRouting(
                employee_id=employee_record.employee_id,
                schedule_id=schedule.schedule_id,
                vehicle_id=vehicle.id,
                pickup_sequence=idx + 1,
                distance_from_last=round(distance, 2),
                cumulative_distance=round(cumulative_distance, 2),
                calculated_pickup_time=calculated_pickup_time,
                pickup_timing_group=pickup_group_time,
                cluster_in_pickup_group=cluster_id,
                pickup_vehicle_assigned_at=datetime.now(),
                on_board_OTP=random.randint(1000, 9999),
                off_board_OTP=random.randint(1000, 9999),
                route_name=route_name,
                route_distance=0  # Set below
            )
            db.session.add(routing)
            cluster_routings.append(routing)
            all_routings.append(routing)

            employee_with_distances.append({
                'employee_id': employee["employee_id"],
                'employee_name': employee["employee_name"],
                'employee_address': employee["employee_address"],
                'pickup_time': employee["pickup_time"],
                'drop_time': employee.get("drop_time"),
                'pickup_sequence': idx + 1,
                'distance_from_last': round(distance, 2),
                'cumulative_distance': round(cumulative_distance, 2),
                'pickup_trip_status': "Routing Done",
                'cluster': cluster_id
            })

        # ✅ Now calculate route distance: first employee → ... → last → office
        route_distance = 0
        for i in range(len(employee_coordinates_chain) - 1):
            route_distance += get_route_distance_km(employee_coordinates_chain[i], employee_coordinates_chain[i + 1])

        # Add last leg: last employee to office
        if employee_coordinates_chain:
            route_distance += get_route_distance_km(employee_coordinates_chain[-1], source_coordinates)

        total_combined_distance += route_distance

        # Set the calculated route distance for this cluster
        for routing in cluster_routings:
            routing.route_distance = round(route_distance, 2)

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": f"DB integrity error: {str(e)}"}), 400

    return jsonify({
        "route": employee_with_distances,
        "total_distance": round(total_combined_distance, 2),
        "vehicle_details": vehicle_details,
        "route_name": route_name,
        "route_distance": round(total_combined_distance, 2)
    }), 200


@home.route('/get/pickup-routing', methods=['POST'])
def get_pickup_routing():
    request_data = request.get_json()
    return handle_pickup_routing(request_data)



#--------------------------------------------------------------------------------------------------------


drop_source_coordinates = [17.441640, 78.381263]  # Office coordinates


def calculate_distance_drop(origin, destination):
    return geodesic(origin, destination).km


def get_drop_vehicle(vehicle_details):
    vehicle = VechileDetails.query.filter_by(vechile_number=vehicle_details.get('vechile_number')).first()
    if not vehicle:
        vehicle = VechileDetails(
            vendor_type=vehicle_details.get('vendor_type'),
            vendor_name=vehicle_details.get('vendor_name'),
            vechile_owner_name=vehicle_details.get('vechile_owner_name'),
            vechile_driver_name=vehicle_details.get('vechile_driver_name'),
            vechile_name=vehicle_details.get('vechile_name'),
            vechile_model=vehicle_details.get('vechile_model'),
            vechile_number=vehicle_details.get('vechile_number'),
            vechile_owner_mobile_no=vehicle_details.get('vechile_owner_mobile_no'),
            vechile_driver_mobile_no=vehicle_details.get('vechile_driver_mobile_no')
        )
        db.session.add(vehicle)
        db.session.commit()
    return vehicle


def insert_drop_employee(employee_data):
    employee = Employees.query.filter_by(employee_id=employee_data['employee_id']).first()
    if not employee:
        employee = Employees(
            employee_id=employee_data['employee_id'],
            employee_name=employee_data['employee_name'],
            employee_address=employee_data['employee_address'],
            latitude=employee_data['employee_coordinates'][0],
            longitude=employee_data['employee_coordinates'][1],
            gender='N/A',
            employee_mobile_no=0,
            employee_email='N/A',
            process='N/A',
            password='N/A',
            role='N/A',
            poc_name='N/A',
            poc_mobile_no=0
        )
        db.session.add(employee)
        db.session.commit()
    return employee


def insert_drop_schedule(employee, schedule_data):
    shift_date = datetime.strptime(schedule_data['shift_date'], '%Y-%m-%d').date()
    schedule = Employees_schedules.query.filter_by(
        employee_id=employee.employee_id,
        shift_date=shift_date
    ).first()

    if not schedule:
        schedule = Employees_schedules(
            employee_id=employee.employee_id,
            shift_date=shift_date,
            pickup_time=datetime.strptime(schedule_data['pickup_time'], '%H:%M:%S').time() if schedule_data.get('pickup_time') else None,
            drop_time=datetime.strptime(schedule_data['drop_time'], '%H:%M:%S').time() if schedule_data.get('drop_time') else None,
            drop_trip_status="Routing Done"
        )
        db.session.add(schedule)
    else:
        schedule.drop_trip_status = "Routing Done"

    db.session.commit()
    return schedule


def handle_drop_routing(request_data):
    if not request_data:
        return jsonify({"error": "Empty request body."}), 400

    shift_key = next(iter(request_data))
    shift_data = request_data[shift_key]

    try:
        drop_group_time = datetime.strptime(shift_key, "%H:%M:%S").time()
    except ValueError:
        drop_group_time = datetime.strptime(shift_key, "%H:%M").time()

    vehicle_details = None
    vehicle = None
    employee_with_distances = []
    all_routings = []
    total_combined_distance = 0  # Total across clusters

    for cluster_data in shift_data:
        cluster_id = cluster_data.get("clusterId")
        route_name = cluster_data.get("routeName")
        if not cluster_id:
            continue

        employee_list = cluster_data.get("employeeList", [])
        if not employee_list:
            continue

        if not vehicle:
            vehicle_details = cluster_data.get("vehicleDetails", {})
            vehicle = get_drop_vehicle(vehicle_details)

        cluster_routings = []
        employee_coordinates_list = [source_coordinates]  # Start at the office
        cumulative_distance = 0
        last_coordinates = source_coordinates

        for idx, employee in enumerate(employee_list):
            employee_coordinates = employee["employee_coordinates"]
            employee_coordinates_list.append(employee_coordinates)

            distance = get_route_distance_km(last_coordinates, employee_coordinates)
            cumulative_distance += distance
            last_coordinates = employee_coordinates

            employee_record = insert_drop_employee(employee)
            schedule = insert_drop_schedule(employee_record, employee)

            try:
                calculated_drop_time = datetime.strptime(employee["calculated_drop_time"], "%H:%M:%S").time()
            except ValueError:
                return jsonify({
                    "error": f"Invalid time format for calculated_drop_time: {employee['calculated_drop_time']}"
                }), 400

            existing_routing = DropRouting.query.filter_by(
                employee_id=employee_record.employee_id,
                schedule_id=schedule.schedule_id,
                vehicle_id=vehicle.id,
                drop_timing_group=drop_group_time,
                cluster_in_drop_group=cluster_id
            ).first()

            if existing_routing:
                return jsonify({
                    "error": f"Routing already exists for employee {employee_record.employee_id} "
                             f"in cluster {cluster_id} at {drop_group_time}."
                }), 400

            routing = DropRouting(
                employee_id=employee_record.employee_id,
                schedule_id=schedule.schedule_id,
                vehicle_id=vehicle.id,
                drop_sequence=idx + 1,
                distance_from_last=round(distance, 2),
                cumulative_distance=round(cumulative_distance, 2),
                calculated_drop_time=calculated_drop_time,
                drop_timing_group=drop_group_time,
                cluster_in_drop_group=cluster_id,
                drop_vehicle_assigned_at=datetime.now(),
                on_board_OTP=random.randint(1000, 9999),
                off_board_OTP=random.randint(1000, 9999),
                route_name=route_name,
                route_distance=0  # Will update
            )
            db.session.add(routing)
            cluster_routings.append(routing)
            all_routings.append(routing)

            employee_with_distances.append({
                'employee_id': employee["employee_id"],
                'employee_name': employee["employee_name"],
                'employee_address': employee["employee_address"],
                'pickup_time': employee["pickup_time"],
                'drop_time': employee.get("drop_time"),
                'drop_sequence': idx + 1,
                'distance_from_last': round(distance, 2),
                'cumulative_distance': round(cumulative_distance, 2),
                'drop_trip_status': "Routing Done",
                'cluster': cluster_id
            })

        # ✅ Route: Office → First Employee → ... → Last Employee
        cluster_route_distance = 0
        for i in range(len(employee_coordinates_list) - 1):
            leg_distance = get_route_distance_km(employee_coordinates_list[i], employee_coordinates_list[i + 1])
            cluster_route_distance += leg_distance

        # ✅ Assign only to this cluster’s routings
        for routing in cluster_routings:
            routing.route_distance = round(cluster_route_distance, 2)

        total_combined_distance += cluster_route_distance

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": f"DB integrity error: {str(e)}"}), 400

    return jsonify({
        "route": employee_with_distances,
        "total_distance": round(total_combined_distance, 2),
        "vehicle_details": vehicle_details,
        "route_name": route_name,
        "route_distance": round(total_combined_distance, 2)
    }), 200



@home.route('/get/drop-routing', methods=['POST'])
def get_drop_routing():
    request_data = request.get_json()
    return handle_drop_routing(request_data)

#---------------------------------------------------------------------------------------------------------




# def get_drop_vehicle(vehicle_details):
#     vehicle = VechileDetails.query.filter_by(vechile_number=vehicle_details.get('vechile_number')).first()
#     if not vehicle:
#         vehicle = VechileDetails(
#             vendor_type=vehicle_details.get('vendor_type'),
#             vendor_name=vehicle_details.get('vendor_name'),
#             vechile_owner_name=vehicle_details.get('vechile_owner_name'),
#             vechile_driver_name=vehicle_details.get('vechile_driver_name'),
#             vechile_name=vehicle_details.get('vechile_name'),
#             vechile_model=vehicle_details.get('vechile_model'),
#             vechile_number=vehicle_details.get('vechile_number'),
#             vechile_owner_mobile_no=vehicle_details.get('vechile_owner_mobile_no'),
#             vechile_driver_mobile_no=vehicle_details.get('vechile_driver_mobile_no')
#         )
#         db.session.add(vehicle)
#         db.session.commit()
#     return vehicle
#
#
# def insert_drop_employee(employee_data):
#     employee = Employees.query.filter_by(employee_id=employee_data['employee_id']).first()
#     if not employee:
#         employee = Employees(
#             employee_id=employee_data['employee_id'],
#             employee_name=employee_data['employee_name'],
#             employee_address=employee_data['employee_address'],
#             latitude=employee_data['employee_coordinates'][0],
#             longitude=employee_data['employee_coordinates'][1],
#             gender='N/A',
#             employee_mobile_no=0,
#             employee_email='N/A',
#             process='N/A',
#             password='N/A',
#             role='N/A',
#             poc_name='N/A',
#             poc_mobile_no=0
#         )
#         db.session.add(employee)
#         db.session.commit()
#     return employee
#
#
# def insert_drop_schedule(employee, schedule_data):
#     shift_date = datetime.strptime(schedule_data['shift_date'], '%Y-%m-%d').date()
#     schedule = Employees_schedules.query.filter_by(
#         employee_id=employee.employee_id,
#         shift_date=shift_date
#     ).first()
#
#     if not schedule:
#         schedule = Employees_schedules(
#             employee_id=employee.employee_id,
#             shift_date=shift_date,
#             pickup_time=datetime.strptime(schedule_data['pickup_time'], '%H:%M:%S').time() if schedule_data.get('pickup_time') else None,
#             drop_time=datetime.strptime(schedule_data['drop_time'], '%H:%M:%S').time() if schedule_data.get('drop_time') else None,
#             drop_trip_status="Routing Done"
#         )
#         db.session.add(schedule)
#     else:
#         schedule.drop_trip_status = "Routing Done"
#
#     db.session.commit()
#     return schedule
#
#
# def handle_drop_routing(request_data):
#     if not request_data:
#         return jsonify({"error": "Empty request body."}), 400
#
#     shift_key = next(iter(request_data))
#     shift_data = request_data[shift_key]
#
#     try:
#         drop_group_time = datetime.strptime(shift_key, "%H:%M:%S").time()
#     except ValueError:
#         drop_group_time = datetime.strptime(shift_key, "%H:%M").time()
#
#     vehicle_details = None
#     vehicle = None
#     employee_with_distances = []
#     cumulative_distance = 0
#     last_coordinates = source_coordinates
#
#     for cluster_data in shift_data:
#         cluster_id = cluster_data.get("clusterId")
#         if not cluster_id:
#             continue
#
#         employee_list = cluster_data.get("employeeList", [])
#         if not employee_list:
#             continue
#
#         if not vehicle:
#             vehicle_details = cluster_data.get("vehicleDetails", {})
#             vehicle = get_drop_vehicle(vehicle_details)
#
#         for idx, employee in enumerate(employee_list):
#             employee_coordinates = employee["employee_coordinates"]
#             distance = calculate_distance(last_coordinates, employee_coordinates)
#             cumulative_distance += distance
#             last_coordinates = employee_coordinates
#
#             employee_record = insert_drop_employee(employee)
#             schedule = insert_drop_schedule(employee_record, employee)
#
#             try:
#                 calculated_drop_time = datetime.strptime(employee["calculated_drop_time"], "%H:%M:%S").time()
#             except ValueError:
#                 return jsonify({
#                     "error": f"Invalid time format for calculated_drop_time: {employee['calculated_drop_time']}"
#                 }), 400
#
#             # ✅ Check for existing drop routing before insert
#             existing_routing = DropRouting.query.filter_by(
#                 employee_id=employee_record.employee_id,
#                 schedule_id=schedule.schedule_id,
#                 vehicle_id=vehicle.id,
#                 drop_timing_group=drop_group_time,
#                 cluster_in_drop_group=cluster_id
#             ).first()
#
#             if existing_routing:
#                 return jsonify({
#                     "error": f"Drop routing already exists for employee {employee_record.employee_id} "
#                              f"in cluster {cluster_id} at {drop_group_time}."
#                 }), 400
#
#             routing = DropRouting(
#                 employee_id=employee_record.employee_id,
#                 schedule_id=schedule.schedule_id,
#                 vehicle_id=vehicle.id,
#                 drop_sequence=idx + 1,
#                 distance_from_last=round(distance, 2),
#                 cumulative_distance=round(cumulative_distance, 2),
#                 calculated_drop_time=calculated_drop_time,
#                 drop_timing_group=drop_group_time,
#                 cluster_in_drop_group=cluster_id,
#                 drop_created_at=datetime.now(),
#                 on_board_OTP=random.randint(1000, 9999),
#                 off_board_OTP=random.randint(1000, 9999),
#             )
#             db.session.add(routing)
#
#             employee_with_distances.append({
#                 'employee_id': employee["employee_id"],
#                 'employee_name': employee["employee_name"],
#                 'employee_address': employee["employee_address"],
#                 'pickup_time': employee["pickup_time"],
#                 'drop_time': employee.get("drop_time"),
#                 'drop_sequence': idx + 1,
#                 'distance_from_last': round(distance, 2),
#                 'cumulative_distance': round(cumulative_distance, 2),
#                 'drop_trip_status': "Routing Done",
#                 'cluster': cluster_id
#             })
#
#     try:
#         db.session.commit()
#     except IntegrityError as e:
#         db.session.rollback()
#         return jsonify({"error": f"DB integrity error: {str(e)}"}), 400
#
#     return jsonify({
#         "route": employee_with_distances,
#         "total_distance": round(cumulative_distance, 2),
#         "vehicle_details": vehicle_details
#     }), 200
#
#
# @home.route('/get/drop-routing', methods=['POST'])
# def get_drop_routing():
#     request_data = request.get_json()
#     return handle_drop_routing(request_data)


#----------------------------------------------------------------------------------------------------------








































