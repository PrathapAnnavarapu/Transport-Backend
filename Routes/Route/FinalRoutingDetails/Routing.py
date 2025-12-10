
from flask import request, jsonify
from Models import db
from Models.Route.Routing.PickupRoutingWithAllEmployees import PickupRouting
from Models.Route.Routing.DropRoutingWithAllEmployess  import DropRouting

from Models.Employee.Employees import Employees
from Models.Vechile.VechileDetails import VechileDetails
from Models.Schedules.Employee_schedules import Employees_schedules
from sqlalchemy.orm import aliased
from datetime import datetime
from Routes import home

@home.route('/get/pickup/routing-details', methods=['POST'])
def get_routing_details_by_cluster():
    try:
        data = request.get_json()
        pickup_times_list = data.get('pickup_time')  # Expect this to be a list
        shift_date_str = data.get('shift_date')

        # Validate input
        if not shift_date_str or not pickup_times_list or not isinstance(pickup_times_list, list):
            return jsonify(success=False, message="Missing or invalid parameters."), 400

        # Convert shift_date
        try:
            shift_date = datetime.strptime(shift_date_str, "%Y-%m-%d").date()
            # Convert each pickup_time string to a time object
            pickup_times = [datetime.strptime(pt, "%H:%M:%S").time() for pt in pickup_times_list]
        except ValueError:
            return jsonify(success=False, message="Invalid date or time format."), 400

        # Query with IN clause for pickup times and status
        routing_data = db.session.query(PickupRouting, Employees, VechileDetails, Employees_schedules) \
            .join(Employees, PickupRouting.employee_id == Employees.employee_id) \
            .join(VechileDetails, PickupRouting.vehicle_id == VechileDetails.id) \
            .join(Employees_schedules, PickupRouting.schedule_id == Employees_schedules.schedule_id) \
            .filter(
                Employees_schedules.shift_date == shift_date,
                Employees_schedules.pickup_time.in_(pickup_times),
                Employees_schedules.pickup_trip_status.in_(['Routing Done', 'Picked Up', 'Completed'])  # Add additional statuses
            ).all()

        # Prepare the result
        result = []
        for routing, employee, vehicle, schedule in routing_data:
            result.append({
                "employee": {
                    "id": employee.employee_id,
                    "name": employee.employee_name,
                    "address": employee.employee_address,
                    "email": employee.employee_email,
                    "mobile_no": employee.employee_mobile_no
                },
                "route_id": routing.id,
                "routing": {
                    "pickup_sequence": routing.pickup_sequence,
                    "calculated_pickup_time": routing.calculated_pickup_time.isoformat() if routing.calculated_pickup_time else None,
                    "cumulative_distance": routing.cumulative_distance,
                    "distance_from_last": routing.distance_from_last,
                    "pickup_trip_status": schedule.pickup_trip_status
                },
                "schedule": {
                    "pickup_time": schedule.pickup_time.isoformat() if schedule and schedule.pickup_time else None,
                    "drop_time": schedule.drop_time.isoformat() if schedule and schedule.drop_time else None,
                    "shift_date": schedule.shift_date.isoformat() if schedule and schedule.shift_date else None,
                    "id": schedule.schedule_id
                },
                "vehicle": {
                    "id": vehicle.id,
                    "name": vehicle.vechile_name,
                    "vechile_number": vehicle.vechile_number,
                    "model": vehicle.vechile_model,
                    "vechile_driver_name": vehicle.vechile_driver_name,
                    "vechile_owner_name": vehicle.vechile_owner_name
                },
                "cluster_id": routing.cluster_in_pickup_group
            })

        return jsonify(success=True, data=result), 200

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500





@home.route('/get/drop/routing-details', methods=['POST'])
def get_drop_routing_details_by_cluster():
    try:
        data = request.get_json()
        drop_times_list = data.get('drop_time')  # Expect this to be a list
        shift_date_str = data.get('shift_date')

        # Validate input
        if not shift_date_str or not drop_times_list or not isinstance(drop_times_list, list):
            return jsonify(success=False, message="Missing or invalid parameters."), 400

        # Convert shift_date
        try:
            shift_date = datetime.strptime(shift_date_str, "%Y-%m-%d").date()
            drop_times = [datetime.strptime(dt, "%H:%M:%S").time() for dt in drop_times_list]
        except ValueError:
            return jsonify(success=False, message="Invalid date or time format."), 400

        # Query for drop routing data, including multiple statuses
        routing_data = db.session.query(DropRouting, Employees, VechileDetails, Employees_schedules) \
            .join(Employees, DropRouting.employee_id == Employees.employee_id) \
            .join(VechileDetails, DropRouting.vehicle_id == VechileDetails.id) \
            .join(Employees_schedules, DropRouting.schedule_id == Employees_schedules.schedule_id) \
            .filter(
                Employees_schedules.shift_date == shift_date,
                Employees_schedules.drop_time.in_(drop_times),
                Employees_schedules.drop_trip_status.in_(['Routing Done', 'Picked Up', 'Completed'])  # Include multiple statuses
            ).all()

        # Prepare the result
        result = []
        for routing, employee, vehicle, schedule in routing_data:
            result.append({
                "employee": {
                    "id": employee.employee_id,
                    "name": employee.employee_name,
                    "address": employee.employee_address,
                    "email": employee.employee_email,
                    "mobile_no": employee.employee_mobile_no
                },
                "route_id": routing.id,
                "routing": {
                    "drop_sequence": routing.drop_sequence,
                    "calculated_drop_time": routing.calculated_drop_time.isoformat() if routing.calculated_drop_time else None,
                    "cumulative_distance": routing.cumulative_distance,
                    "distance_from_last": routing.distance_from_last,
                    "drop_trip_status": schedule.drop_trip_status
                },
                "schedule": {
                    "pickup_time": schedule.pickup_time.isoformat() if schedule and schedule.pickup_time else None,
                    "drop_time": schedule.drop_time.isoformat() if schedule and schedule.drop_time else None,
                    "shift_date": schedule.shift_date.isoformat() if schedule and schedule.shift_date else None,
                    "id": schedule.schedule_id
                },
                "vehicle": {
                    "id": vehicle.id,
                    "name": vehicle.vechile_name,
                    "vechile_number": vehicle.vechile_number,
                    "model": vehicle.vechile_model,
                    "vechile_driver_name": vehicle.vechile_driver_name,
                    "vechile_owner_name": vehicle.vechile_owner_name
                },
                "cluster_id": routing.cluster_in_drop_group
            })

        return jsonify(success=True, data=result), 200

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

































































@home.route('/get/pickup-routing-details/all', methods=['POST'])
def get_each_cluster_routing_details():
    data = request.get_json()
    pickup_time = data.get('pickup_time')
    cluster_id = data.get('cluster_id')
    shift_date = data.get('shift_date')

    if not all([shift_date, pickup_time, cluster_id]):
        return jsonify(success=False, message="Missing required query parameters."), 400

    Employee = aliased(Employees)
    Vehicle = aliased(VechileDetails)
    Schedule = aliased(Employees_schedules)

    routing_data = db.session.query(PickupRouting, Employee, Vehicle, Schedule) \
        .outerjoin(Employee, PickupRouting.employee_id == Employee.employee_id) \
        .outerjoin(Vehicle, PickupRouting.vehicle_id == Vehicle.id) \
        .outerjoin(Schedule, PickupRouting.schedule_id == Schedule.schedule_id) \
        .filter(Schedule.shift_date == shift_date) \
        .filter(Schedule.pickup_time == pickup_time) \
        .filter(PickupRouting.cluster_in_pickup_group == cluster_id) \
        .order_by(PickupRouting.pickup_sequence) \
        .all()

    matched_data = []

    for routing, employee, vehicle, schedule in routing_data:
        matched_data.append({
            "employee": {
                "id": employee.employee_id,
                "name": employee.employee_name,
                "address": employee.employee_address,
                "email": employee.employee_email,
                "mobile_no": employee.employee_mobile_no
            },
            "route_id": routing.id,
            "routing": {
                "pickup_sequence": routing.pickup_sequence,
                "pickup_time": str(routing.calculated_pickup_time),
                "cumulative_distance": routing.cumulative_distance,
                "distance_from_last": routing.distance_from_last,
                "pickup_trip_status": schedule.pickup_trip_status  # ✅ FIX: Use correct field from schedule
            },
            "schedule": {
                "pickup_time": str(schedule.pickup_time),
                "drop_time": str(schedule.drop_time),
                "shift_date": str(schedule.shift_date),
                "id": schedule.schedule_id
            },
            "vehicle": {
                "id": vehicle.id,
                "name": vehicle.vechile_name,
                "number": vehicle.vechile_number,
                "model": vehicle.vechile_model,
                "driver_name": vehicle.vechile_driver_name
            }
        })

    if matched_data:
        return jsonify(success=True, data=matched_data), 200
    else:
        return jsonify(success=False, message="No cluster data found for provided inputs."), 404



























@home.route('/get/pickup-routing-details/by-date', methods=['POST'])
def get_routing_by_date():
    data = request.get_json()
    shift_date = data.get('shift_date')

    if not shift_date:
        return jsonify(success=False, message="Shift date is required."), 400

    Employee = aliased(Employees)
    Vehicle = aliased(VechileDetails)
    Schedule = aliased(Employees_schedules)

    routing_data = db.session.query(PickupRouting, Employee, Vehicle, Schedule) \
        .outerjoin(Employee, PickupRouting.employee_id == Employee.employee_id) \
        .outerjoin(Vehicle, PickupRouting.vehicle_id == Vehicle.id) \
        .outerjoin(Schedule, PickupRouting.schedule_id == Schedule.schedule_id) \
        .filter(Schedule.shift_date == shift_date) \
        .order_by(PickupRouting.pickup_timing_group, PickupRouting.cluster_in_pickup_group, PickupRouting.pickup_sequence) \
        .all()

    result = []
    for routing, employee, vehicle, schedule in routing_data:
        result.append({
            "employee": {
                "id": employee.employee_id,
                "name": employee.employee_name,
                "address": employee.employee_address,
                "email": employee.employee_email,
                "mobile_no": employee.employee_mobile_no
            },
            "vehicle": {
                "id": vehicle.id,
                "name": vehicle.vechile_name,
                "number": vehicle.vechile_number,
                "model": vehicle.vechile_model,
                "driver_name": vehicle.vechile_driver_name
            },
            "schedule": {
                "pickup_time": str(schedule.pickup_time),
                "drop_time": str(schedule.drop_time),
                "shift_date": str(schedule.shift_date)
            },
            "routing": {
                "pickup_time": str(routing.calculated_pickup_time),
                "pickup_sequence": routing.pickup_sequence,
                "distance_from_last": routing.distance_from_last,
                "cumulative_distance": routing.cumulative_distance,
                "trip_status": routing.trip_status,
                "cluster": routing.cluster_in_pickup_group
            }
        })

    return jsonify(success=True, data=result), 200



