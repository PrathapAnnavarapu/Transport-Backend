from Models import db
from datetime import datetime
from flask import request, jsonify

from Models.Route.Routing.DropRoutingWithAllEmployess import DropRouting
from Models.Schedules.Employee_schedules import Employees_schedules
from Routes.TripBilling.DropTripBillings import calculate_fare_and_create_bill_for_drop
from Routes import home
import pytz

# Set timezone
ist = pytz.timezone('Asia/Kolkata')


def check_and_finalize_trip(vehicle_id, schedule_id):
    trip_entries = DropRouting.query.filter_by(
        vehicle_id=vehicle_id,
    ).all()

    if not trip_entries:
        return False  # No trip found

    all_dropped = all(entry.off_board_OTP_entered_at is not None for entry in trip_entries)

    if all_dropped:
        #print(f"Trip complete for vehicle {vehicle_id} schedule {schedule_id}")
        # trigger_billing(vehicle_id, schedule_id)
        #print("Trip Completed")
        calculate_fare_and_create_bill_for_drop(vehicle_id, schedule_id)
        return True

    return False


@home.route('/employee/drop/offboard', methods=['POST'])
def drop_offboard_employee():
    data = request.json
    routing_id = data['routing_id']
    otp = data['otp']


    routing = DropRouting.query.get(routing_id)
    if not routing:
        return jsonify({"error": "Routing not found"}), 404

    if routing.off_board_OTP == otp:
        # ✅ Save time in IST
        routing.off_board_OTP_entered_at = datetime.now(ist)


        # ✅ Update drop trip status
        schedule = Employees_schedules.query.get(routing.schedule_id)
        if schedule:
            schedule.drop_trip_status = 'Completed'

        db.session.commit()

        # ✅ Trigger trip finalization
        check_and_finalize_trip(routing.vehicle_id, routing.schedule_id)

        return jsonify({"message": "OTP verified and employee off-boarded"}), 200

    return jsonify({"error": "Invalid OTP"}), 400


@home.route('/employee/drop/onboard', methods=['POST'])
def drop_onboard_employee():
    data = request.json

    routing_id = data['routing_id']
    otp = data['otp']
    entered_by = data.get('entered_by')

    routing = DropRouting.query.get(routing_id)

    if not routing:
        return jsonify({"error": "Routing not found"}), 404

    if routing.on_board_OTP == otp:
        routing.on_board_OTP_entered_at = datetime.now(ist)
        routing.OTP_entered_by = entered_by

        # ✅ Update pickup trip status
        schedule = Employees_schedules.query.get(routing.schedule_id)
        if schedule:
            schedule.drop_trip_status = 'Picked Up'

        db.session.commit()
        return jsonify({"message": "OTP verified and employee onboarded"}), 200

    return jsonify({"error": "Invalid OTP"}), 400
