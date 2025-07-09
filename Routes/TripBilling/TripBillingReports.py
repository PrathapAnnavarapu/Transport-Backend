
from flask import jsonify, request
from Models import db
from Models.Route.Routing.PickupRoutingWithAllEmployees import PickupRouting
from Models.Route.Routing.DropRoutingWithAllEmployess import DropRouting
from Models.TripBilling.PickupTripBillings import PickupTripBilling
from Models.TripBilling.DropTripBillings import DropTripBilling
from Models.TripBilling.PickupTripEmployeeLink import PickupTripEmployeeLink
from Models.TripBilling.DropTripEmployeeLink import DropTripEmployeeLink
from sqlalchemy.orm import joinedload
from datetime import datetime, date
from Routes import home



# @home.route('/get/billing-report', methods=['GET'])
# def get_billing_report():
#     trip_type = request.args.get('trip_type', 'all')
#     vehicle_id = request.args.get('vehicle_id')
#
#     pickup_query = db.session.query(PickupTripBilling).options(
#         db.joinedload(PickupTripBilling.vehicle),
#         db.joinedload(PickupTripBilling.employees)
#             .joinedload(PickupTripEmployeeLink.pickup_routing)
#             .joinedload(PickupRouting.employee),
#         db.joinedload(PickupTripBilling.employees)
#             .joinedload(PickupTripEmployeeLink.pickup_routing)
#             .joinedload(PickupRouting.schedule)
#     )
#
#     drop_query = db.session.query(DropTripBilling).options(
#         db.joinedload(DropTripBilling.vehicle),
#         db.joinedload(DropTripBilling.employees)
#             .joinedload(DropTripEmployeeLink.drop_routing)
#             .joinedload(DropRouting.employee),
#         db.joinedload(DropTripBilling.employees)
#             .joinedload(DropTripEmployeeLink.drop_routing)
#             .joinedload(DropRouting.schedule)
#     )
#
#     if vehicle_id and vehicle_id != 'all':
#         pickup_query = pickup_query.filter(PickupTripBilling.vehicle_id == int(vehicle_id))
#         drop_query = drop_query.filter(DropTripBilling.vehicle_id == int(vehicle_id))
#
#     data = []
#
#     if trip_type in ['pickup', 'all']:
#         pickup_billings = pickup_query.all()
#         for billing in pickup_billings:
#             employee_list = []
#             seen_employee_ids = set()
#             assigned_times = []
#             started_times = []
#             ended_times = []
#             pickup_times = set()
#             shift_dates = set()
#
#             for link in billing.employees:
#                 routing = link.pickup_routing
#                 if not routing or not routing.employee:
#                     continue
#
#                 employee = routing.employee
#                 schedule = routing.schedule
#
#                 if employee.employee_id in seen_employee_ids:
#                     continue
#                 seen_employee_ids.add(employee.employee_id)
#
#                 if routing.pickup_vehicle_assigned_at:
#                     assigned_times.append(routing.pickup_vehicle_assigned_at)
#                 if routing.on_board_OTP_entered_at:
#                     started_times.append(routing.on_board_OTP_entered_at)
#                 if routing.off_board_OTP_entered_at:
#                     ended_times.append(routing.off_board_OTP_entered_at)
#                 if routing.pickup_timing_group:
#                     pickup_times.add(str(routing.pickup_timing_group))
#                 if schedule and schedule.shift_date:
#                     shift_dates.add(str(schedule.shift_date))
#
#                 employee_list.append({
#                     "employee_id": employee.employee_id,
#                     "employee_name": employee.employee_name,
#                     "pickup_sequence": routing.pickup_sequence,
#                     "distance_from_last": routing.distance_from_last
#                 })
#
#             data.append({
#                 "trip_id": billing.id,
#                 "trip_type": "Pickup",
#                 "trip_date": billing.trip_date.strftime("%Y-%m-%d %H:%M:%S"),
#                 "vehicle_number": billing.vehicle.vechile_number,
#                 "vehicle_owner_name": billing.vehicle.vechile_owner_name,
#                 "route_name": billing.route_name,
#                 "fare_amount": billing.fare_amount,
#                 "status": billing.status,
#                 "distance_travelled": billing.distance_travelled,
#                 "billing_mode": billing.billing_mode,
#                 "vehicle_assigned_at": min(assigned_times) if assigned_times else None,
#                 "trip_started_at": min(started_times) if started_times else None,
#                 "trip_ended_at": max(ended_times) if ended_times else None,
#                 "pickup_times": list(pickup_times),
#                 "shift_dates": list(shift_dates),
#                 "employees": employee_list
#             })
#
#     if trip_type in ['drop', 'all']:
#         drop_billings = drop_query.all()
#         for billing in drop_billings:
#             employee_list = []
#             seen_employee_ids = set()
#             assigned_times = []
#             started_times = []
#             ended_times = []
#             drop_times = set()
#             shift_dates = set()
#
#             for link in billing.employees:
#                 routing = link.drop_routing
#                 if not routing or not routing.employee:
#                     continue
#
#                 employee = routing.employee
#                 schedule = routing.schedule
#
#                 if employee.employee_id in seen_employee_ids:
#                     continue
#                 seen_employee_ids.add(employee.employee_id)
#
#                 if routing.drop_vehicle_assigned_at:
#                     assigned_times.append(routing.drop_vehicle_assigned_at)
#                 if routing.on_board_OTP_entered_at:
#                     started_times.append(routing.on_board_OTP_entered_at)
#                 if routing.off_board_OTP_entered_at:
#                     ended_times.append(routing.off_board_OTP_entered_at)
#                 if routing.drop_timing_group:
#                     drop_times.add(str(routing.drop_timing_group))
#                 if schedule and schedule.shift_date:
#                     shift_dates.add(str(schedule.shift_date))
#
#                 employee_list.append({
#                     "employee_id": employee.employee_id,
#                     "employee_name": employee.employee_name,
#                     "drop_sequence": routing.drop_sequence,
#                     "distance_from_last": routing.distance_from_last
#                 })
#
#             data.append({
#                 "trip_id": billing.id,
#                 "trip_type": "Drop",
#                 "trip_date": billing.trip_date.strftime("%Y-%m-%d %H:%M:%S"),
#                 "vehicle_number": billing.vehicle.vechile_number,
#                 "vehicle_owner_name": billing.vehicle.vechile_owner_name,
#                 "route_name": billing.route_name,
#                 "fare_amount": billing.fare_amount,
#                 "status": billing.status,
#                 "distance_travelled": billing.distance_travelled,
#                 "billing_mode": billing.billing_mode,
#                 "vehicle_assigned_at": min(assigned_times) if assigned_times else None,
#                 "trip_started_at": min(started_times) if started_times else None,
#                 "trip_ended_at": max(ended_times) if ended_times else None,
#                 "drop_times": list(drop_times),
#                 "shift_dates": list(shift_dates),
#                 "employees": employee_list
#             })
#
#     return jsonify(data)


from sqlalchemy.orm import selectinload

@home.route('/get/billing-report', methods=['GET'])
def get_billing_report():
    trip_type = request.args.get('trip_type', 'all')
    vehicle_id = request.args.get('vehicle_id')

    pickup_query = db.session.query(PickupTripBilling).options(
        selectinload(PickupTripBilling.vehicle),
        selectinload(PickupTripBilling.employees)
            .selectinload(PickupTripEmployeeLink.pickup_routing)
            .selectinload(PickupRouting.employee),
        selectinload(PickupTripBilling.employees)
            .selectinload(PickupTripEmployeeLink.pickup_routing)
            .selectinload(PickupRouting.schedule)
    )

    drop_query = db.session.query(DropTripBilling).options(
        selectinload(DropTripBilling.vehicle),
        selectinload(DropTripBilling.employees)
            .selectinload(DropTripEmployeeLink.drop_routing)
            .selectinload(DropRouting.employee),
        selectinload(DropTripBilling.employees)
            .selectinload(DropTripEmployeeLink.drop_routing)
            .selectinload(DropRouting.schedule)
    )

    if vehicle_id and vehicle_id != 'all':
        pickup_query = pickup_query.filter(PickupTripBilling.vehicle_id == int(vehicle_id))
        drop_query = drop_query.filter(DropTripBilling.vehicle_id == int(vehicle_id))

    data = []

    if trip_type in ['pickup', 'all']:
        pickup_billings = pickup_query.all()
        for billing in pickup_billings:
            employee_list = []
            seen_employee_ids = set()
            assigned_times = []
            started_times = []
            ended_times = []
            pickup_times = set()
            shift_dates = set()

            for link in billing.employees:
                routing = link.pickup_routing
                if not routing or not routing.employee:
                    continue

                employee = routing.employee
                schedule = routing.schedule

                if employee.employee_id in seen_employee_ids:
                    continue
                seen_employee_ids.add(employee.employee_id)

                if routing.pickup_vehicle_assigned_at:
                    assigned_times.append(routing.pickup_vehicle_assigned_at)
                if routing.on_board_OTP_entered_at:
                    started_times.append(routing.on_board_OTP_entered_at)
                if routing.off_board_OTP_entered_at:
                    ended_times.append(routing.off_board_OTP_entered_at)
                if routing.pickup_timing_group:
                    pickup_times.add(str(routing.pickup_timing_group))
                if schedule and schedule.shift_date:
                    shift_dates.add(str(schedule.shift_date))

                employee_list.append({
                    "employee_id": employee.employee_id,
                    "employee_name": employee.employee_name,
                    "pickup_sequence": routing.pickup_sequence,
                    "distance_from_last": routing.distance_from_last
                })

            data.append({
                "trip_id": billing.id,
                "trip_type": "Pickup",
                "trip_date": billing.trip_date.strftime("%Y-%m-%d %H:%M:%S"),
                "vehicle_number": billing.vehicle.vechile_number,
                "vehicle_owner_name": billing.vehicle.vechile_owner_name,
                "route_name": billing.route_name,
                "fare_amount": billing.fare_amount,
                "status": billing.status,
                "distance_travelled": billing.distance_travelled,
                "billing_mode": billing.billing_mode,
                "vehicle_assigned_at": min(assigned_times) if assigned_times else None,
                "trip_started_at": min(started_times) if started_times else None,
                "trip_ended_at": max(ended_times) if ended_times else None,
                "pickup_times": list(pickup_times),
                "shift_dates": list(shift_dates),
                "employees": employee_list
            })

    if trip_type in ['drop', 'all']:
        drop_billings = drop_query.all()
        for billing in drop_billings:
            employee_list = []
            seen_employee_ids = set()
            assigned_times = []
            started_times = []
            ended_times = []
            drop_times = set()
            shift_dates = set()

            for link in billing.employees:
                routing = link.drop_routing
                if not routing or not routing.employee:
                    continue

                employee = routing.employee
                schedule = routing.schedule

                if employee.employee_id in seen_employee_ids:
                    continue
                seen_employee_ids.add(employee.employee_id)

                if routing.drop_vehicle_assigned_at:
                    assigned_times.append(routing.drop_vehicle_assigned_at)
                if routing.on_board_OTP_entered_at:
                    started_times.append(routing.on_board_OTP_entered_at)
                if routing.off_board_OTP_entered_at:
                    ended_times.append(routing.off_board_OTP_entered_at)
                if routing.drop_timing_group:
                    drop_times.add(str(routing.drop_timing_group))
                if schedule and schedule.shift_date:
                    shift_dates.add(str(schedule.shift_date))

                employee_list.append({
                    "employee_id": employee.employee_id,
                    "employee_name": employee.employee_name,
                    "drop_sequence": routing.drop_sequence,
                    "distance_from_last": routing.distance_from_last
                })

            data.append({
                "trip_id": billing.id,
                "trip_type": "Drop",
                "trip_date": billing.trip_date.strftime("%Y-%m-%d %H:%M:%S"),
                "vehicle_number": billing.vehicle.vechile_number,
                "vehicle_owner_name": billing.vehicle.vechile_owner_name,
                "route_name": billing.route_name,
                "fare_amount": billing.fare_amount,
                "status": billing.status,
                "distance_travelled": billing.distance_travelled,
                "billing_mode": billing.billing_mode,
                "vehicle_assigned_at": min(assigned_times) if assigned_times else None,
                "trip_started_at": min(started_times) if started_times else None,
                "trip_ended_at": max(ended_times) if ended_times else None,
                "drop_times": list(drop_times),
                "shift_dates": list(shift_dates),
                "employees": employee_list
            })

    return jsonify(data)










@home.route('/get/todays-billing-report', methods=['GET'])
def get_todays_billing_report():
    today = date.today()
    trip_type = request.args.get('trip_type', 'all')
    vehicle_id = request.args.get('vehicle_id')

    pickup_query = db.session.query(PickupTripBilling).options(
        joinedload(PickupTripBilling.vehicle),
        joinedload(PickupTripBilling.employees)
            .joinedload(PickupTripEmployeeLink.pickup_routing)
            .joinedload(PickupRouting.employee),
        joinedload(PickupTripBilling.employees)
            .joinedload(PickupTripEmployeeLink.pickup_routing)
            .joinedload(PickupRouting.schedule)
    ).filter(db.func.date(PickupTripBilling.trip_date) == today)

    drop_query = db.session.query(DropTripBilling).options(
        joinedload(DropTripBilling.vehicle),
        joinedload(DropTripBilling.employees)
            .joinedload(DropTripEmployeeLink.drop_routing)
            .joinedload(DropRouting.employee),
        joinedload(DropTripBilling.employees)
            .joinedload(DropTripEmployeeLink.drop_routing)
            .joinedload(DropRouting.schedule)
    ).filter(db.func.date(DropTripBilling.trip_date) == today)

    if vehicle_id and vehicle_id != 'all':
        pickup_query = pickup_query.filter(PickupTripBilling.vehicle_id == int(vehicle_id))
        drop_query = drop_query.filter(DropTripBilling.vehicle_id == int(vehicle_id))

    data = []

    if trip_type in ['pickup', 'all']:
        for billing in pickup_query.all():
            employee_list = []
            seen_employee_ids = set()
            shift_dates = set()
            pickup_times = set()
            assigned_times = []
            started_times = []
            ended_times = []

            for link in billing.employees:
                routing = link.pickup_routing
                if not routing or not routing.employee:
                    continue
                employee = routing.employee
                schedule = routing.schedule

                if employee.employee_id not in seen_employee_ids:
                    seen_employee_ids.add(employee.employee_id)
                    employee_list.append({
                        "employee_id": employee.employee_id,
                        "employee_name": employee.employee_name,
                        "pickup_sequence": routing.pickup_sequence,
                        "distance_from_last": routing.distance_from_last
                    })

                if schedule and schedule.shift_date:
                    shift_dates.add(str(schedule.shift_date))
                if routing.pickup_timing_group:
                    pickup_times.add(str(routing.pickup_timing_group))
                if routing.pickup_vehicle_assigned_at:
                    assigned_times.append(routing.pickup_vehicle_assigned_at)
                if routing.on_board_OTP_entered_at:
                    started_times.append(routing.on_board_OTP_entered_at)
                if routing.off_board_OTP_entered_at:
                    ended_times.append(routing.off_board_OTP_entered_at)

            data.append({
                "trip_id": billing.id,
                "trip_type": "Pickup",
                "trip_date": billing.trip_date.strftime("%Y-%m-%d %H:%M:%S"),
                "vehicle_number": billing.vehicle.vechile_number,
                "vehicle_owner_name": billing.vehicle.vechile_owner_name,
                "route_name": billing.route_name,
                "fare_amount": billing.fare_amount,
                "status": billing.status,
                "distance_travelled": billing.distance_travelled,
                "billing_mode": billing.billing_mode,
                "vehicle_assigned_at": min(assigned_times) if assigned_times else None,
                "trip_started_at": min(started_times) if started_times else None,
                "trip_ended_at": max(ended_times) if ended_times else None,
                "pickup_times": list(pickup_times),
                "shift_dates": list(shift_dates),
                "employees": employee_list
            })

    if trip_type in ['drop', 'all']:
        for billing in drop_query.all():
            employee_list = []
            seen_employee_ids = set()
            shift_dates = set()
            drop_times = set()
            assigned_times = []
            started_times = []
            ended_times = []

            for link in billing.employees:
                routing = link.drop_routing
                if not routing or not routing.employee:
                    continue
                employee = routing.employee
                schedule = routing.schedule

                if employee.employee_id not in seen_employee_ids:
                    seen_employee_ids.add(employee.employee_id)
                    employee_list.append({
                        "employee_id": employee.employee_id,
                        "employee_name": employee.employee_name,
                        "drop_sequence": routing.drop_sequence,
                        "distance_from_last": routing.distance_from_last
                    })

                if schedule and schedule.shift_date:
                    shift_dates.add(str(schedule.shift_date))
                if routing.drop_timing_group:
                    drop_times.add(str(routing.drop_timing_group))
                if routing.drop_vehicle_assigned_at:
                    assigned_times.append(routing.drop_vehicle_assigned_at)
                if routing.on_board_OTP_entered_at:
                    started_times.append(routing.on_board_OTP_entered_at)
                if routing.off_board_OTP_entered_at:
                    ended_times.append(routing.off_board_OTP_entered_at)

            data.append({
                "trip_id": billing.id,
                "trip_type": "Drop",
                "trip_date": billing.trip_date.strftime("%Y-%m-%d %H:%M:%S"),
                "vehicle_number": billing.vehicle.vechile_number,
                "vehicle_owner_name": billing.vehicle.vechile_owner_name,
                "route_name": billing.route_name,
                "fare_amount": billing.fare_amount,
                "status": billing.status,
                "distance_travelled": billing.distance_travelled,
                "billing_mode": billing.billing_mode,
                "vehicle_assigned_at": min(assigned_times) if assigned_times else None,
                "trip_started_at": min(started_times) if started_times else None,
                "trip_ended_at": max(ended_times) if ended_times else None,
                "drop_times": list(drop_times),
                "shift_dates": list(shift_dates),
                "employees": employee_list
            })
    return jsonify(data)



@home.route('/billing-reports/bulk-update', methods=['POST'])
def bulk_update():
    data = request.get_json()
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    status = data.get('status')

    if not start_date or not end_date or not status:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Convert dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Perform bulk update
        db.session.query(PickupTripBilling).filter(
            PickupTripBilling.trip_date.between(start_date, end_date)
        ).update({'status': status}, synchronize_session=False)

        db.session.query(DropTripBilling).filter(
            DropTripBilling.trip_date.between(start_date, end_date)
        ).update({'status': status}, synchronize_session=False)

        db.session.commit()
        return jsonify({'message': 'Records updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500












