from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from Models import db
from Models.Vechile.VechileDetails import VechileDetails
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


@home.route('/create/vechile', methods=['POST'])
def create_vechile_details():
    data = request.get_json()
    new_vechile = VechileDetails(vendor_type=data['vendor_type'], vendor_name= data['vendor_name'],vechile_owner_name=data['vechile_owner_name'], vechile_driver_name=data['vechile_driver_name'], vechile_name= data['vechile_name'], vechile_model=data['vechile_model'], vechile_number = data['vechile_number'], vechile_owner_mobile_no=data['vechile_owner_mobile_no'], vechile_driver_mobile_no=data['vechile_driver_mobile_no'], vechile_owner_address=data['vechile_owner_address'], vechile_driver_address=data['vechile_driver_address'], billing_mode=data['billing_mode'], billing_policy_id=data['billing_policy_id'] )
    db.session.add(new_vechile)
    db.session.commit()
    return jsonify({'message': 'Vechile added successfully'}), 201



@home.route('get/vechile/all', methods=['GET'])
#@jwt_required()
def get_vechile_all():
    data = VechileDetails.query.all()  # Assuming you're sending JSON data
    users_list = [{'id': vechile.id, 'vendor_type': vechile.vendor_type, 'vendor_name':vechile.vendor_name, 'vechile_owner_name':vechile.vechile_owner_name, 'vechile_driver_name': vechile.vechile_driver_name, 'vechile_name' :vechile.vechile_name, 'vechile_model': vechile.vechile_model, 'vechile_number':vechile.vechile_number, 'vechile_owner_mobile_no':vechile.vechile_owner_mobile_no, 'vechile_driver_mobile_no':vechile.vechile_driver_mobile_no, 'vechile_owner_address':vechile.vechile_owner_address, 'billing_mode':vechile.billing_mode} for vechile in data]
    return jsonify(users_list), 200




# @home.route('/employee/update/<int:employee_id>', methods=['PUT'])
# # @role_required('Admin' and 'hughes_employee')
# def update_user(employee_id):
#     data = request.get_json()  # Assuming you're sending JSON data
#     user = Employees.query.get(employee_id)
#     if not user:
#         return jsonify({'message': 'User not found'}), 404
#
#     user.username = data.get('username', user.username)
#     user.email = data.get('email', user.email)
#     db.session.commit()
#     return jsonify({'message': 'User updated successfully'}), 200
#
# @home.route('/users/delete/<int:employee_id>', methods=['DELETE'])
# #@jwt_required()
# def delete_employee(employee_id):
#     user = Employees.query.get(employee_id)
#     if not user:
#         return jsonify({'message': 'User not found'}), 404
#
#     db.session.delete(user)
#     db.session.commit()
#     return jsonify({'message': 'User deleted successfully'}), 200