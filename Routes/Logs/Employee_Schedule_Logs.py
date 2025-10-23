
from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.orm import joinedload
from Models import db
from Models.Schedules.Employee_schedules import Employees_schedules
from Models.Logs.EmployeeSchedulesLogs import EmployeeScheduleLogs
from Models.Employee.Employees import Employees
from Routes import home

from datetime import datetime

@home.route('/employee/schedules-with-logs', methods=['POST'])
@jwt_required()
def get_employee_schedules_with_logs_range():
    data = request.get_json()

    employee_id = data.get("employee_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not employee_id or not start_date or not end_date:
        return jsonify({"message": "employee_id, start_date, and end_date are required"}), 400

    # Convert dates
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format, use YYYY-MM-DD"}), 400

    # JWT check
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    if current_user_id != employee_id and claims.get("role") == "user":
        return jsonify({"message": "Unauthorized"}), 403

    schedules_with_logs = []

    # 1️⃣ Query schedules + logs
    schedules = (
        db.session.query(Employees_schedules)
        .options(
            joinedload(Employees_schedules.employee),
            joinedload(Employees_schedules.logs)
        )
        .filter(
            Employees_schedules.employee_id == employee_id,
            Employees_schedules.shift_date >= start_date,
            Employees_schedules.shift_date <= end_date
        )
        .all()
    )

    for schedule in schedules:
        # 🟢 Pickup record
        pickup_logs = [
            {
                "log_id": log.log_id,
                "action": log.action,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "created_by_id": log.created_by_id,
                "created_by_name": log.created_by_name,
                "notes": log.notes,
                "request_source": log.request_source
            }
            for log in schedule.logs
            if log.action.startswith("pickup_")
        ]

        if schedule.pickup_time or schedule.pickup_trip_status or pickup_logs:
            schedules_with_logs.append({
                "schedule_id": schedule.schedule_id,
                "trip_type": "pickup",
                "shift_date": str(schedule.shift_date),
                "shift_time": str(schedule.shift_time) if hasattr(schedule, "shift_time") else None,
                "shift_type": getattr(schedule, "shift_type", None),
                "time": str(schedule.pickup_time) if schedule.pickup_time else None,
                "status": schedule.pickup_trip_status,
                "employee": {
                    "employee_id": schedule.employee.employee_id,
                    "employee_name": schedule.employee.employee_name,
                    "employee_email": schedule.employee.employee_email,
                    "home_area": getattr(schedule.employee, 'home_area', ''),
                    "employee_address": getattr(schedule.employee, 'employee_address', '')
                },
                "logs": pickup_logs
            })

        # 🔵 Drop record
        drop_logs = [
            {
                "log_id": log.log_id,
                "action": log.action,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "created_by_id": log.created_by_id,
                "created_by_name": log.created_by_name,
                "notes": log.notes,
                "request_source": log.request_source
            }
            for log in schedule.logs
            if log.action.startswith("drop_")
        ]

        if schedule.drop_time or schedule.drop_trip_status or drop_logs:
            schedules_with_logs.append({
                "schedule_id": schedule.schedule_id,
                "trip_type": "drop",
                "shift_date": str(schedule.shift_date),
                "shift_time": str(schedule.shift_time) if hasattr(schedule, "shift_time") else None,
                "shift_type": getattr(schedule, "shift_type", None),
                "time": str(schedule.drop_time) if schedule.drop_time else None,
                "status": schedule.drop_trip_status,
                "employee": {
                    "employee_id": schedule.employee.employee_id,
                    "employee_name": schedule.employee.employee_name,
                    "employee_email": schedule.employee.employee_email,
                    "home_area": getattr(schedule.employee, 'home_area', ''),
                    "employee_address": getattr(schedule.employee, 'employee_address', '')
                },
                "logs": drop_logs
            })

    # 2️⃣ Query standalone deleted logs
    deleted_logs = (
        db.session.query(EmployeeScheduleLogs)
        .filter(
            EmployeeScheduleLogs.created_by_id == employee_id,
            EmployeeScheduleLogs.created_at >= start_date,
            EmployeeScheduleLogs.created_at <= end_date,
            EmployeeScheduleLogs.action.in_(["pickup_deleted", "drop_deleted"])
        )
        .all()
    )

    for log in deleted_logs:
        schedules_with_logs.append({
            "schedule_id": None,
            "trip_type": "pickup" if log.action.startswith("pickup_") else "drop",
            "shift_date": log.created_at.date().isoformat() if log.created_at else None,
            "shift_time": None,     # ❌ Not available anymore
            "shift_type": None,     # ❌ Not available anymore
            "time": None,
            "status": "Deleted",
            "employee": {
                "employee_id": log.created_by_id,
                "employee_name": log.created_by_name,
                "employee_email": ""
            },
            "logs": [{
                "log_id": log.log_id,
                "action": log.action,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "created_by_id": log.created_by_id,
                "created_by_name": log.created_by_name,
                "notes": log.notes,
                "request_source": log.request_source
            }]
        })

    return jsonify({
        "employee_id": employee_id,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "schedules": schedules_with_logs
    }), 200



#
# @home.route('/employee/schedules-with-logs', methods=['POST'])
# @jwt_required()
# def get_employee_schedules_with_logs_range():
#     data = request.get_json()
#
#     employee_id = data.get("employee_id")
#     start_date = data.get("start_date")
#     end_date = data.get("end_date")
#
#     if not employee_id or not start_date or not end_date:
#         return jsonify({"message": "employee_id, start_date, and end_date are required"}), 400
#
#     # Convert dates
#     try:
#         start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
#         end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
#     except ValueError:
#         return jsonify({"message": "Invalid date format, use YYYY-MM-DD"}), 400
#
#     # JWT check
#     current_user_id = get_jwt_identity()
#     claims = get_jwt()
#     if current_user_id != employee_id and claims.get("role") == "user":
#         return jsonify({"message": "Unauthorized"}), 403
#
#     # Query schedules + employee + logs
#     schedules = (
#         db.session.query(Employees_schedules)
#         .options(
#             joinedload(Employees_schedules.employee),
#             joinedload(Employees_schedules.logs)
#         )
#         .filter(
#             Employees_schedules.employee_id == employee_id,
#             Employees_schedules.shift_date >= start_date,
#             Employees_schedules.shift_date <= end_date
#         )
#         .all()
#     )
#
#     if not schedules:
#         return jsonify({"message": "No schedules found in given range"}), 404
#
#     schedules_with_logs = []
#
#     for schedule in schedules:
#         # 🟢 Pickup record
#         if schedule.pickup_time or schedule.pickup_trip_status:
#             pickup_logs = [
#                 {
#                     "log_id": log.log_id,
#                     "action": log.action,
#                     "created_at": log.created_at.isoformat() if log.created_at else None,
#                     "created_by_id": log.created_by_id,
#                     "created_by_name": log.created_by_name,
#                     "notes": log.notes,
#                     "request_source": log.request_source
#                 }
#                 for log in schedule.logs
#                 if log.action.startswith("pickup_")  # ✅ only pickup-related logs
#             ]
#
#             schedules_with_logs.append({
#                 "schedule_id": schedule.schedule_id,
#                 "trip_type": "pickup",  # ✅ now clear
#                 "shift_date": str(schedule.shift_date),
#                 "time": str(schedule.pickup_time) if schedule.pickup_time else None,
#                 "status": schedule.pickup_trip_status,
#                 "employee": {
#                     "employee_id": schedule.employee.employee_id,
#                     "employee_name": schedule.employee.employee_name,
#                     "employee_email": schedule.employee.employee_email,
#                     "home_area": getattr(schedule.employee, 'home_area', ''),
#                     "employee_address": getattr(schedule.employee, 'employee_address', '')
#                 },
#                 "logs": pickup_logs
#             })
#
#         # 🔵 Drop record
#         if schedule.drop_time or schedule.drop_trip_status:
#             drop_logs = [
#                 {
#                     "log_id": log.log_id,
#                     "action": log.action,
#                     "created_at": log.created_at.isoformat() if log.created_at else None,
#                     "created_by_id": log.created_by_id,
#                     "created_by_name": log.created_by_name,
#                     "notes": log.notes,
#                     "request_source": log.request_source
#                 }
#                 for log in schedule.logs
#                 if log.action.startswith("drop_")  # ✅ only drop-related logs
#             ]
#
#             schedules_with_logs.append({
#                 "schedule_id": schedule.schedule_id,
#                 "trip_type": "drop",  # ✅ now clear
#                 "shift_date": str(schedule.shift_date),
#                 "time": str(schedule.drop_time) if schedule.drop_time else None,
#                 "status": schedule.drop_trip_status,
#                 "employee": {
#                     "employee_id": schedule.employee.employee_id,
#                     "employee_name": schedule.employee.employee_name,
#                     "employee_email": schedule.employee.employee_email,
#                     "home_area": getattr(schedule.employee, 'home_area', ''),
#                     "employee_address": getattr(schedule.employee, 'employee_address', '')
#                 },
#                 "logs": drop_logs
#             })
#
#     return jsonify({
#         "employee_id": employee_id,
#         "start_date": str(start_date),
#         "end_date": str(end_date),
#         "schedules": schedules_with_logs
#     }), 200

