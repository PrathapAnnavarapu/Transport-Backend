from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import json
# Role-based access decorator
import pandas as pd
from datetime import datetime, timedelta
from Models.Logs.EmployeeSchedulesLogs import EmployeeScheduleLogs
from Models import db
from Models.Schedules.Employee_schedules import Employees_schedules
from Models.Employee.Employees import Employees
from Routes import home


def log_schedule_action(schedule_id, action, user_id, user_name, notes=None):
    log_entry = EmployeeScheduleLogs(
        schedule_id=schedule_id,
        action=action,
        created_by_id=user_id,
        created_by_name=user_name,
        notes=notes
    )
    db.session.add(log_entry)
    db.session.commit()




def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != required_role:
                return jsonify({"message": "Access forbidden: insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator





@home.route('/create/employee/pickup-schedules', methods=['POST'])
@jwt_required()
def create_pickup_schedules():
    data = request.get_json()

    request_source = request.headers.get("X-Request-Source", "Web")  # default Web if not sent

    required_fields = ['employee_id', 'shift_date', 'pickup_time']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'{field} is required'}), 400

    employee_id = data['employee_id']
    shift_date = data['shift_date']
    pickup_time = data['pickup_time']
    pickup_status = data.get('pickup_trip_status', "Confirmed")

    # ✅ Get logged-in user info from JWT
    created_by_id = get_jwt_identity()       # string employee_id
    claims = get_jwt()                       # dict of additional claims
    created_by_name = claims.get("employee_name")

    # Check if schedule exists
    existing_schedule = Employees_schedules.query.filter_by(
        employee_id=employee_id,
        shift_date=shift_date
    ).first()

    if existing_schedule:
        existing_schedule.pickup_time = pickup_time
        existing_schedule.pickup_trip_status = pickup_status

        log = EmployeeScheduleLogs(
            schedule=existing_schedule,
            action="pickup_updated",
            created_by_id=created_by_id,
            created_by_name=created_by_name,
            notes=f"Pickup updated to {pickup_time}, status: {pickup_status}",
            request_source = request_source
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'message': 'Pickup updated successfully'}), 200

    new_schedule = Employees_schedules(
        employee_id=employee_id,
        shift_date=shift_date,
        pickup_time=pickup_time,
        pickup_trip_status=pickup_status
    )
    db.session.add(new_schedule)
    db.session.flush()

    log = EmployeeScheduleLogs(
        schedule=new_schedule,
        action="pickup_created",
        created_by_id=created_by_id,
        created_by_name=created_by_name,
        notes=f"Pickup scheduled at {pickup_time}, status: {pickup_status}",
        request_source=request_source
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': 'Pickup scheduled successfully'}), 201







# Get all employee schedules
@home.route('/get/employee-schedules/all', methods=['GET'])
# @jwt_required()
def get_schedules():
    data = db.session.query(Employees, Employees_schedules).outerjoin(
        Employees_schedules, Employees.employee_id == Employees_schedules.employee_id).all()

    employees_dict = {}
    for employees, schedules in data:
        if employees.employee_id not in employees_dict:
            employees_dict[employees.employee_id] = {
                'employee_id': employees.employee_id,
                'employee_name': employees.employee_name,
                'employee_address': employees.employee_address,
                'schedules': []
            }
        if schedules:
            employees_dict[employees.employee_id]['schedules'].append({
                'schedule_id': schedules.schedule_id,
                'shift_date': schedules.shift_date.isoformat() if schedules.shift_date else None,
                'pickup_time': schedules.pickup_time.isoformat() if schedules.pickup_time else None,
                'drop_time': schedules.drop_time.isoformat() if schedules.drop_time else None,
                'pickup_trip_status': schedules.pickup_trip_status,
                'drop_trip_status': schedules.drop_trip_status
            })

    users_list = list(employees_dict.values())
    return jsonify(users_list), 200


from flask import request, jsonify

@home.route('/get/spoc-employee-schedules/all', methods=['GET'])
# @jwt_required()
def get_spoc_schedules():
    spoc_name = request.args.get("spocName")  # ✅ get SPOC name from query params

    query = db.session.query(Employees, Employees_schedules).outerjoin(
        Employees_schedules, Employees.employee_id == Employees_schedules.employee_id
    )

    if spoc_name:  # ✅ filter by spocName if provided
        query = query.filter(Employees.poc_name == spoc_name)

    data = query.all()

    employees_dict = {}
    for employees, schedules in data:
        if employees.employee_id not in employees_dict:
            employees_dict[employees.employee_id] = {
                'employee_id': employees.employee_id,
                'employee_name': employees.employee_name,
                'employee_address': employees.employee_address,
                'schedules': []
            }
        if schedules:
            employees_dict[employees.employee_id]['schedules'].append({
                'schedule_id': schedules.schedule_id,
                'shift_date': schedules.shift_date.isoformat() if schedules.shift_date else None,
                'pickup_time': schedules.pickup_time.isoformat() if schedules.pickup_time else None,
                'drop_time': schedules.drop_time.isoformat() if schedules.drop_time else None,
                'pickup_trip_status': schedules.pickup_trip_status,
                'drop_trip_status': schedules.drop_trip_status
            })

    users_list = list(employees_dict.values())
    return jsonify(users_list), 200



# Get schedules for a specific employee
@home.route('/get/employee-schedules/self/<int:employee_id>', methods=['GET'])
# @jwt_required()  # Uncomment if you want to require JWT authentication
def get_employee_schedule(employee_id):
    data = db.session.query(Employees, Employees_schedules).outerjoin(
        Employees_schedules, Employees.employee_id == Employees_schedules.employee_id
    ).filter(Employees.employee_id == employee_id).all()

    # Check if employee exists
    if not data:
        return jsonify({"error": "Employee not found or no schedules available"}), 404

    employee_dict = {}
    for employees, schedules in data:
        if employees.employee_id not in employee_dict:
            employee_dict[employees.employee_id] = {
                'employee_id': employees.employee_id,
                'employee_name': employees.employee_name,
                'employee_address': employees.employee_address,
                'schedules': []
            }
        if schedules:
            employee_dict[employees.employee_id]['schedules'].append({
                'schedule_id': schedules.schedule_id,
                'shift_date': schedules.shift_date.isoformat() if schedules.shift_date else None,
                'pickup_time': schedules.pickup_time.isoformat() if schedules.pickup_time else None,
                'drop_time': schedules.drop_time.isoformat() if schedules.drop_time else None,
                'pickup_trip_status': schedules.pickup_trip_status,
                'drop_trip_status': schedules.drop_trip_status
            })

    employee_data = list(employee_dict.values())  # Since employee_id is unique, we can directly access the first element
    return jsonify(employee_data), 200


# Delete Pickup Schedule Route
@home.route('/employee/pickup-schedule/delete/<int:employee_id>/<string:date>', methods=['DELETE'])
@jwt_required()
def delete_pickup_schedule(employee_id, date):
    # Find the schedule with the specified employee_id and shift_date
    schedule_to_update = Employees_schedules.query.filter_by(
        employee_id=employee_id,
        shift_date=date
    ).first()

    if not schedule_to_update:
        return jsonify({'message': 'Schedule not found'}), 404

    # ✅ Get logged-in user info from JWT
    created_by_id = get_jwt_identity()       # string employee_id
    claims = get_jwt()                       # dict of additional claims
    created_by_name = claims.get("employee_name")
    request_source = request.headers.get("X-Request-Source", "Web")

    try:
        # Keep old values for logs
        old_pickup_time = schedule_to_update.pickup_time
        old_pickup_status = schedule_to_update.pickup_trip_status

        # Set pickup_time & status to NULL
        schedule_to_update.pickup_time = None
        schedule_to_update.pickup_trip_status = None

        # ✅ Add log
        log = EmployeeScheduleLogs(
            schedule=schedule_to_update,
            action="pickup_deleted",
            created_by_id=created_by_id,
            created_by_name=created_by_name,
            notes=f"Pickup deleted (was {old_pickup_time}, status: {old_pickup_status})",
            request_source=request_source
        )
        db.session.add(log)

        db.session.commit()
        return jsonify({'message': 'Pickup time deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'An error occurred: {e}'}), 500


# Drop Routes

# Create Drop Schedule Route
@home.route('/create/employee/drop-schedules', methods=['POST'])
@jwt_required()
def create_drop_schedules():
    data = request.get_json()
    request_source = request.headers.get("X-Request-Source", "Web")  # default Web if not sent

    # ✅ Required fields
    required_fields = ['employee_id', 'shift_date', 'drop_time']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'{field} is required'}), 400

    employee_id = data['employee_id']
    shift_date = data['shift_date']
    drop_time = data['drop_time']
    drop_status = data.get('drop_trip_status', "Confirmed")

    # ✅ Get logged-in user info from JWT
    created_by_id = get_jwt_identity()       # string employee_id
    claims = get_jwt()                       # dict of additional claims
    created_by_name = claims.get("employee_name")

    # ✅ Find schedule for that employee & date
    schedule = Employees_schedules.query.filter_by(
        employee_id=employee_id,
        shift_date=shift_date
    ).first()

    if schedule:
        if schedule.drop_time is None:
            # 🟢 First time drop is being created
            schedule.drop_time = drop_time
            schedule.drop_trip_status = drop_status

            log = EmployeeScheduleLogs(
                schedule=schedule,
                action="drop_created",
                created_by_id=created_by_id,
                created_by_name=created_by_name,
                notes=f"Drop scheduled at {drop_time}, status: {drop_status}",
                request_source=request_source
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({'message': 'Drop created successfully'}), 201
        else:
            # 🔵 Drop already exists → update
            old_time = schedule.drop_time
            old_status = schedule.drop_trip_status

            schedule.drop_time = drop_time
            schedule.drop_trip_status = drop_status

            log = EmployeeScheduleLogs(
                schedule=schedule,
                action="drop_updated",
                created_by_id=created_by_id,
                created_by_name=created_by_name,
                notes=f"Drop updated from {old_time} ({old_status}) to {drop_time} ({drop_status})",
                request_source=request_source
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({'message': 'Drop updated successfully'}), 200

    # 🆕 No schedule row exists yet → create new schedule
    new_schedule = Employees_schedules(
        employee_id=employee_id,
        shift_date=shift_date,
        drop_time=drop_time,
        drop_trip_status=drop_status
    )
    db.session.add(new_schedule)
    db.session.flush()  # to get new_schedule.id

    log = EmployeeScheduleLogs(
        schedule=new_schedule,
        action="drop_created",
        created_by_id=created_by_id,
        created_by_name=created_by_name,
        notes=f"Drop scheduled at {drop_time}, status: {drop_status}",
        request_source=request_source
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': 'Drop created successfully'}), 201



# Delete Drop Schedule Route
@home.route('/employee/drop-schedule/delete/<int:employee_id>/<string:date>', methods=['DELETE'])
@jwt_required()
def delete_drop_schedule(employee_id, date):
    # Find the schedule with the specified employee_id and shift_date
    schedule_to_update = Employees_schedules.query.filter_by(
        employee_id=employee_id,
        shift_date=date
    ).first()

    if not schedule_to_update:
        return jsonify({'message': 'Schedule not found'}), 404

    # ✅ Get logged-in user info from JWT
    created_by_id = get_jwt_identity()       # string employee_id
    claims = get_jwt()                       # dict of additional claims
    created_by_name = claims.get("employee_name")
    request_source = request.headers.get("X-Request-Source", "Web")

    try:
        # Keep old values for logs
        old_drop_time = schedule_to_update.drop_time
        old_drop_status = schedule_to_update.drop_trip_status

        # Set drop_time & status to NULL
        schedule_to_update.drop_time = None
        schedule_to_update.drop_trip_status = None

        # ✅ Add log
        log = EmployeeScheduleLogs(
            schedule=schedule_to_update,
            action="drop_deleted",
            created_by_id=created_by_id,
            created_by_name=created_by_name,
            notes=f"Drop deleted (was {old_drop_time}, status: {old_drop_status})",
            request_source=request_source
        )
        db.session.add(log)

        db.session.commit()
        return jsonify({'message': 'Drop time deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'An error occurred: {e}'}), 500





@home.route('/upload/schedules/matrix', methods=['POST'])
def upload_schedules_matrix():
    import pandas as pd
    from datetime import datetime
    from sqlalchemy.exc import SQLAlchemyError

    def is_valid_time(val):
        if pd.isna(val):
            return False
        if isinstance(val, datetime):  # Excel might parse times as datetime
            return True
        try:
            datetime.strptime(str(val).strip(), "%H:%M:%S")
            return True
        except Exception:
            return False

    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    try:
        df = pd.read_excel(file, engine='openpyxl', skiprows=[1])  # Skip the "PICKUP"/"DROP" row
    except Exception as e:
        return jsonify({'message': f'Error reading Excel file: {str(e)}'}), 400

    # Strip column headers
    df.columns = df.columns.map(lambda x: str(x).strip())

    base_cols = ['Employee Id', 'Employee Name']
    schedule_cols = [col for col in df.columns if col not in base_cols]

    for _, row in df.iterrows():
        employee_id = str(row.get('Employee Id')).strip()

        if not employee_id or employee_id.lower() == 'nan':
            continue  # Skip empty or malformed IDs

        for i in range(0, len(schedule_cols), 2):
            pickup_col = schedule_cols[i]
            drop_col = schedule_cols[i + 1] if i + 1 < len(schedule_cols) else None

            try:
                shift_date = datetime.strptime(pickup_col.strip(), "%d-%m-%Y").date()
            except ValueError:
                continue  # Skip bad date headers

            pickup_time = row.get(pickup_col)
            drop_time = row.get(drop_col) if drop_col else None

            # Clean time values
            pickup_time_str = None
            if is_valid_time(pickup_time):
                if isinstance(pickup_time, datetime):
                    pickup_time_str = pickup_time.time()
                else:
                    pickup_time_str = datetime.strptime(str(pickup_time), "%H:%M:%S").time()

            drop_time_str = None
            if is_valid_time(drop_time):
                if isinstance(drop_time, datetime):
                    drop_time_str = drop_time.time()
                else:
                    drop_time_str = datetime.strptime(str(drop_time), "%H:%M:%S").time()

            # Skip rows with no time values
            if not pickup_time_str and not drop_time_str:
                continue

            try:
                existing = Employees_schedules.query.filter_by(
                    employee_id=employee_id,
                    shift_date=shift_date
                ).first()

                if existing:
                    if pickup_time_str:
                        existing.pickup_time = pickup_time_str
                        existing.pickup_trip_status = "Confirmed"
                    if drop_time_str:
                        existing.drop_time = drop_time_str
                        existing.drop_trip_status = "Confirmed"
                else:
                    new_schedule = Employees_schedules(
                        employee_id=employee_id,
                        shift_date=shift_date,
                        pickup_time=pickup_time_str,
                        drop_time=drop_time_str,
                        pickup_trip_status="Confirmed" if pickup_time_str else None,
                        drop_trip_status="Confirmed" if drop_time_str else None
                    )
                    db.session.add(new_schedule)
            except SQLAlchemyError as db_err:
                print(f"DB error for employee {employee_id} on {shift_date}: {db_err}")
                continue

    db.session.commit()
    return jsonify({'message': 'Schedules processed successfully'}), 200








# def role_required(*allowed_roles):
#     def decorator(fn):
#         @wraps(fn)
#         @jwt_required()
#         def wrapper(*args, **kwargs):
#             current_user = get_jwt_identity()
#             user_role = current_user.get('role')
#             if user_role not in allowed_roles:
#                 return jsonify({"message": "Access forbidden: insufficient permissions"}), 403
#             return fn(*args, **kwargs)
#         return wrapper
#     return decorator
#
#
#
# # Create Pickup Schedule Route
# @home.route('/create/employee/pickup-schedules', methods=['POST'])
# @role_required('admin', 'user', 'superUser')
# def create_pickup_schedules():
#     print("Headers:", request.headers)
#     print("Content-Type:", request.content_type)
#     print("Raw body:", request.data)
#     print("Parsed JSON:", request.get_json())
#     data = request.get_json()
#     current_user = get_jwt_identity()
#
#     required_fields = ['employee_id', 'shift_date', 'pickup_time']
#     for field in required_fields:
#         if field not in data:
#             return jsonify({'message': f'{field} is required'}), 400
#
#     existing_schedule = Employees_schedules.query.filter_by(
#         employee_id=data['employee_id'],
#         shift_date=data['shift_date']
#     ).first()
#
#     if existing_schedule:
#         if data.get('pickup_time'):
#             existing_schedule.pickup_time = data['pickup_time']
#             db.session.commit()
#
#             # ✅ log update
#             log_schedule_action(
#                 schedule_id=existing_schedule.schedule_id,
#                 action='pickup_updated',
#                 user_id=current_user['id'],
#                 user_name=current_user['name'],
#                 notes=f"Pickup time updated to {data['pickup_time']}"
#             )
#             return jsonify({'message': 'Pickup Scheduled successfully'}), 200
#         else:
#             return jsonify({'message': 'No pickup time provided to update'}), 400
#
#     employee_schedules = Employees_schedules(
#         employee_id=data['employee_id'],
#         shift_date=data['shift_date'],
#         pickup_time=data['pickup_time'],
#         pickup_trip_status=data.get('pickup_trip_status', "Confirmed")
#     )
#     db.session.add(employee_schedules)
#     db.session.commit()
#
#     # ✅ log create
#     log_schedule_action(
#         schedule_id=employee_schedules.schedule_id,
#         action='pickup_created',
#         user_id=current_user['id'],
#         user_name=current_user['name'],
#         notes='New pickup schedule created'
#     )
#
#     return jsonify({'message': 'Pickup scheduled successfully'}), 201