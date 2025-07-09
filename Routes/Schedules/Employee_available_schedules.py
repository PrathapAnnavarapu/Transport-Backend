
from flask import jsonify, request
from Models.Schedules.Employee_available_schedules import Employees_available_schedules
from Models import db
from Routes import home
from datetime import datetime


@home.route('/employees/available/pickup-schedules/all', methods=['GET'])
def get_available_pickup_schedules():
    # Query to get all pickup schedules and order them by pickup_time in ascending order
    data = Employees_available_schedules.query.order_by(Employees_available_schedules.pickup_time).all()

    # Convert the results to a list of dictionaries
    pickup_times_list = [{'id': schedule.id, 'pickup_time': schedule.pickup_time.isoformat()} for schedule in data]

    return jsonify(pickup_times_list), 200


@home.route('/employees/available/drop-schedules/all', methods=['GET'])
def get_available_drop_schedules():
    # Query to get all drop schedules and order them by drop_time in ascending order
    data = Employees_available_schedules.query.order_by(Employees_available_schedules.drop_time).all()

    # Convert the results to a list of dictionaries
    drop_times_list = [{'id': schedule.id, 'drop_time': schedule.drop_time.isoformat()} for schedule in data]

    return jsonify(drop_times_list), 200


@home.route('/employees/available/schedule/add', methods=['POST'])
def add_schedule():
    data = request.get_json()
    pickup_time = datetime.strptime(data['pickup_time'], '%H:%M').time()
    drop_time = datetime.strptime(data['drop_time'], '%H:%M').time()

    schedule = Employees_available_schedules(pickup_time=pickup_time, drop_time=drop_time)
    db.session.add(schedule)
    db.session.commit()

    return jsonify({'message': 'Schedule added'}), 201


@home.route('/employees/available/schedule/<int:schedule_id>/delete', methods=['POST'])
def delete_schedule(schedule_id):
    schedule = Employees_available_schedules.query.get(schedule_id)
    if not schedule:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(schedule)
    db.session.commit()
    return jsonify({'message': 'Schedule deleted'}), 200

