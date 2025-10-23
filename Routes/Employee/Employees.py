from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from geopy.geocoders import Nominatim
import pandas as pd
import json
from werkzeug.utils import secure_filename
import os
from Models import db
from Models.Employee.Employees import Employees
from Routes import home


def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            if current_user['role'] != required_role:
                return jsonify({"message": "Access forbidden: insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator




ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@home.route('/upload/employees', methods=['POST'])
def upload_employees():
    """Handle file upload and process employee data."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    print("Received file:", file.filename)  # Debugging: print file name

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only .xlsx or .csv files are allowed'}), 400

    try:
        # Check file extension to determine how to read the file
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        if file_extension == 'xlsx':
            df = pd.read_excel(file)
        elif file_extension == 'csv':
            # Try reading the CSV file and handle parsing errors
            try:
                df = pd.read_csv(file)
            except pd.errors.ParserError as e:
                print(f"❌ Error parsing CSV: {str(e)}")
                return jsonify({'error': f"Error parsing CSV: {str(e)}"}), 400

        # Debugging: print the first few rows of the file
        print("First few rows of the file:", df.head())

        # Define the required columns
        required_columns = [
            'employee_name', 'employee_address', 'employee_email', 'gender',
            'employee_mobile_no', 'employee_id', 'role', 'process',
            'poc_name', 'poc_mobile_no', 'Geocode', 'home_area', 'active_status', 'work_location'
        ]

        # Check if all required columns are present
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Missing columns: {missing_columns}")  # Debugging: log missing columns
            return jsonify({'error': f'Missing columns: {", ".join(missing_columns)}'}), 400

        # Process the data from CSV
        employees = []
        for _, row in df.iterrows():
            try:
                # Attempt to parse Geocode into latitude and longitude
                geo = str(row['Geocode']).split(',')
                latitude = float(geo[0].strip()) if len(geo) > 0 else None
                longitude = float(geo[1].strip()) if len(geo) > 1 else None
                print(f"Parsed geocode at row {_ + 2}: {latitude}, {longitude}")  # Debugging: print parsed geocode
            except Exception as geo_err:
                print(f"Error in geocode format at row {_ + 2}: {geo_err}")  # Debugging: log geocode parsing error
                return jsonify({'error': f'Invalid Geocode format at row {_ + 2}'}), 400

            # Create employee record
            user = Employees(
                employee_name=row['employee_name'],
                employee_address=row['employee_address'],
                employee_email=row['employee_email'],
                gender=row['gender'],
                employee_mobile_no=str(row['employee_mobile_no']),
                employee_id=row['employee_id'],
                role=row['role'],
                process=row['process'],
                poc_name=row.get('poc_name', ''),
                poc_mobile_no=str(row.get('poc_mobile_no', '')),
                latitude=latitude,
                longitude=longitude,
                home_area=row['home_area'],
                active_status=row['active_status'],
                work_location=row['work_location']


            )
            employees.append(user)

        # Insert data into the database
        db.session.bulk_save_objects(employees)
        db.session.commit()

        return jsonify({'message': f'{len(employees)} employees added successfully'}), 201

    except Exception as e:
        print(f"❌ Error: {str(e)}")  # Debugging: log errors
        return jsonify({'error': 'Error processing the file', 'details': str(e)}), 500




@home.route('add/new/employee', methods=['POST'])
def add():
    data = request.get_json()  # Assuming you're sending JSON data

    if not data:
        return jsonify({'error': 'req data is empty'}), 400

    new_user = Employees(employee_name=data['employee_name'], employee_address= data['employee_address'],employee_email=data['employee_email'], gender= data['gender'], employee_mobile_no=data['employee_mobile_no'], employee_id = data['employee_id'], role=data['role'], process=data['process'], poc_name=data['poc_name'], poc_mobile_no=data['poc_mobile_no'], latitude=data['latitude'], longitude=data['longitude'], home_area=data['home_area'], active_status=data['active_status'], work_location=data['work_location'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Employee added successfully'}), 201


@home.route('/signup/employee', methods=['POST'])
def set_password():
    data = request.get_json()

    phone = data.get('phone')
    new_password = data.get('password')

    if not phone or not new_password:
        return jsonify({'error': 'Mobile number and password are required'}), 400

    user = Employees.query.filter_by(employee_mobile_no=phone).first()

    if not user:
        return jsonify({'error': 'Employee not found'}), 404

    user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()

    return jsonify({'message': 'Password updated successfully'}), 200



@home.route('/employee/login', methods=['POST'])
def login():
    data = request.get_json()
    phone_no = data.get('phone')
    password = data.get('password')

    if not phone_no or not password:
        return jsonify({'message': 'Phone number and password are required'}), 400

    user = Employees.query.filter_by(employee_mobile_no=phone_no).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    if not user.password:
        return jsonify({'message': 'Please set a password to login'}), 403

    if check_password_hash(user.password, password):
        # ✅ Identity must be a simple type (str/int)
        identity = str(user.employee_id)

        # Store the rest of user info in additional_claims
        additional_claims = {
            "employee_name": user.employee_name,
            "employee_email": user.employee_email,
            "role": user.role,
            "work_location":user.work_location
        }

        access_token = create_access_token(identity=identity, additional_claims=additional_claims)
        return jsonify(access_token=access_token, ok=True), 200

    return jsonify({'message': 'Invalid credentials'}), 401


@home.route('/employees/all', methods=['GET', 'OPTIONS'])
@jwt_required(optional=True)
def get_users():
    print(dict(request.headers))
    if request.method == 'OPTIONS':
        return '', 200
    claims = get_jwt()  # contains additional_claims set during token creation
    location = claims.get('work_location')
    data = Employees.query.filter_by(work_location=location).all()

    users_list = [{'id': e.id, 'employee_name': e.employee_name, 'employee_id': e.employee_id,
                   'employee_address': e.employee_address, 'employee_mobile_no': e.employee_mobile_no,
                   'gender': e.gender, 'employee_email': e.employee_email, 'role': e.role, 'process':e.process,
                   'poc_name':e.poc_name, 'poc_mobile_no':e.poc_mobile_no, 'active_status':e.active_status,
                   'home_area':e.home_area, 'work_location':e.work_location} for e in data]
    return jsonify(users_list), 200



@home.route('/get/employee', methods=['GET'])
def get_employee_by_id():
    employee_id = request.args.get('employeeId')

    if not employee_id:
        return jsonify({'error': 'Missing employeeId parameter'}), 400

    employee = Employees.query.filter_by(employee_id=employee_id).first()

    if not employee:
        return jsonify({'error': f'No employee found with employeeId {employee_id}'}), 404

    return jsonify({
        'id': employee.id,
        'employee_name': employee.employee_name,
        'employee_id': employee.employee_id,
        'employee_address': employee.employee_address,
        'employee_mobile_no': employee.employee_mobile_no,
        'gender': employee.gender,
        'employee_email': employee.employee_email,
        'role': employee.role,
        'process': employee.process,
        'poc_name': employee.poc_name,
        'poc_mobile_no': employee.poc_mobile_no,
        'latitude': employee.latitude,
        'longitude':employee.longitude
    }), 200


@home.route('/employee/update/<employee_id>', methods=['PUT'])
def update_user(employee_id):
    data = request.get_json()

    # Use filter_by because query.get expects primary key of exact type
    user = Employees.query.filter_by(employee_id=employee_id).first()

    print(user)  # Should now print the user object or None

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Update fields as before...
    user.employee_name = data.get('employee_name', user.employee_name)
    user.employee_email = data.get('employee_email', user.employee_email)
    user.latitude = data.get('latitude', user.latitude)
    user.longitude = data.get('longitude', user.longitude)
    user.employee_address = data.get('employee_address', user.employee_address)
    user.role = data.get('role', user.role)
    user.gender = data.get('gender', user.gender)
    user.employee_mobile_no = data.get('employee_mobile_no', user.employee_mobile_no)

    user.process = data.get('process', user.process)
    user.poc_name = data.get('poc_name', user.poc_name)
    user.poc_mobile_no = data.get('poc_mobile_no', user.poc_mobile_no)

    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200


@home.route('/users/delete/<int:employee_id>', methods=['DELETE'])
#@jwt_required()
def delete_employee(employee_id):
    user = Employees.query.get(employee_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200