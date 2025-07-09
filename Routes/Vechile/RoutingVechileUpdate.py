from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, time

from Models import db
from Models.Route.Routing.DropRoutingWithAllEmployess import DropRouting
from Models.Route.Routing.PickupRoutingWithAllEmployees import PickupRouting
from Routes import home


@home.route('/update/pickup-vehicles', methods=['POST'])
def update_pickup_vehicle():
    try:
        data = request.get_json()  # This will give you the entire payload
        print("Received payload:", data)  # Log the payload to verify it

        # Your update logic here
        for item in data:
            employee_id = item['employee_id']
            schedule_id = item['schedule_id']
            vehicle_id = item['vehicle_id']

            # Ensure the employee_id and schedule_id combination exists
            routing = PickupRouting.query.filter_by(employee_id=employee_id, schedule_id=schedule_id).first()
            if routing:
                routing.vehicle_id = vehicle_id
                db.session.commit()
            else:
                print(f"Routing not found for {employee_id} and schedule {schedule_id}")

        return jsonify({"status": "success", "message": "Vehicle updated successfully."}), 200

    except Exception as e:
        db.session.rollback()  # In case of error, rollback the session
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@home.route('/update/drop-vehicles', methods=['POST'])
def update_drop_vehicle():
    try:
        data = request.get_json()  # This will give you the entire payload
        print("Received payload:", data)  # Log the payload to verify it

        # Your update logic here
        for item in data:
            employee_id = item['employee_id']
            schedule_id = item['schedule_id']
            vehicle_id = item['vehicle_id']

            # Ensure the employee_id and schedule_id combination exists
            routing = DropRouting.query.filter_by(employee_id=employee_id, schedule_id=schedule_id).first()
            if routing:
                routing.vehicle_id = vehicle_id
                db.session.commit()
            else:
                print(f"Routing not found for {employee_id} and schedule {schedule_id}")

        return jsonify({"status": "success", "message": "Vehicle updated successfully."}), 200

    except Exception as e:
        db.session.rollback()  # In case of error, rollback the session
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500







