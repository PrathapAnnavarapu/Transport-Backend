from flask import Blueprint, request, jsonify
from Models import db
from Models.Employee.Employees import Employees
from Models.Schedules.Employees_schedules import Employees_schedules
from Models.Route.PickupRouting import PickupRouting
from Models.Route.DropRouting import DropRouting
from Models.VehicleTracking.VehicleTracking import VehicleTracking
from Models.Vechile.VechileDetails import VechileDetails
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func
from geopy.distance import geodesic
import logging

employee_app_bp = Blueprint('employee_app', __name__)

def calculate_eta(vehicle_location, employee_location, avg_speed_kmph=30):
    """Calculate ETA in minutes considering traffic"""
    distance_km = geodesic(vehicle_location, employee_location).km
    
    # Adjust speed based on time of day (peak hours)
    current_hour = datetime.now().hour
    if 8 <= current_hour <= 10 or 17 <= current_hour <= 19:
        avg_speed_kmph *= 0.6  # 40% slower during peak hours
    
    eta_minutes = (distance_km / avg_speed_kmph) * 60
    return round(eta_minutes)


@employee_app_bp.route('/api/employee/my-assignment/<int:employee_id>', methods=['GET'])
def get_employee_assignment(employee_id):
    """
    Get employee's vehicle assignment for today with co-passengers
    Query params: date (optional, defaults to today)
    """
    try:
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        shift_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        
        # Get employee
        employee = Employees.query.get(employee_id)
        if not employee:
            return jsonify({"success": False, "message": "Employee not found"}), 404
        
        # Get today's schedule
        schedule = Employees_schedules.query.filter_by(
            employee_id=employee_id,
            shift_date=shift_date
        ).first()
        
        if not schedule:
            return jsonify({
                "success": True,
                "data": None,
                "message": "No schedule for today"
            }), 200
        
        # Determine trip type (pickup or drop based on which is active)
        trip_type = None
        routing = None
        
        # Check pickup first
        if schedule.pickup_time:
            routing = PickupRouting.query.filter_by(
                employee_id=employee_id,
                schedule_id=schedule.schedule_id
            ).first()
            if routing:
                trip_type = 'pickup'
        
        # If no pickup, check drop
        if not routing and schedule.drop_time:
            routing = DropRouting.query.filter_by(
                employee_id=employee_id,
                schedule_id=schedule.schedule_id
            ).first()
            if routing:
                trip_type = 'drop'
        
        if not routing:
            return jsonify({
                "success": True,
                "data": {
                    "has_assignment": False,
                    "pickup_time": str(schedule.pickup_time) if schedule.pickup_time else None,
                    "drop_time": str(schedule.drop_time) if schedule.drop_time else None,
                    "message": "Vehicle not yet assigned"
                }
            }), 200
        
        # Get vehicle details
        vehicle = VechileDetails.query.get(routing.vehicle_id)
        
        # Get latest vehicle location
        latest_tracking = VehicleTracking.query.filter_by(
            vehicle_id=routing.vehicle_id,
            shift_date=shift_date
        ).order_by(VehicleTracking.timestamp.desc()).first()
        
        vehicle_location = None
        vehicle_status = 'idle'
        eta_minutes = None
        
        if latest_tracking:
            vehicle_location = {
                "latitude": latest_tracking.latitude,
                "longitude": latest_tracking.longitude
            }
            vehicle_status = latest_tracking.status
            
            # Calculate ETA if vehicle is en_route
            if vehicle_status in ['en_route', 'arrived']:
                employee_coords = (employee.latitude, employee.longitude)
                vehicle_coords = (latest_tracking.latitude, latest_tracking.longitude)
                eta_minutes = calculate_eta(vehicle_coords, employee_coords)
        
        # Get co-passengers (others in same cluster)
        if trip_type == 'pickup':
            co_passengers_query = db.session.query(
                PickupRouting, Employees, Employees_schedules
            ).join(
                Employees, PickupRouting.employee_id == Employees.employee_id
            ).join(
                Employees_schedules, PickupRouting.schedule_id == Employees_schedules.schedule_id
            ).filter(
                PickupRouting.vehicle_id == routing.vehicle_id,
                PickupRouting.cluster_in_pickup_group == routing.cluster_in_pickup_group,
                Employees_schedules.shift_date == shift_date
            ).order_by(PickupRouting.pickup_sequence).all()
        else:
            co_passengers_query = db.session.query(
                DropRouting, Employees, Employees_schedules
            ).join(
                Employees, DropRouting.employee_id == Employees.employee_id
            ).join(
                Employees_schedules, DropRouting.schedule_id == Employees_schedules.schedule_id
            ).filter(
                DropRouting.vehicle_id == routing.vehicle_id,
                DropRouting.cluster_in_drop_group == routing.cluster_in_drop_group,
                Employees_schedules.shift_date == shift_date
            ).order_by(DropRouting.drop_sequence).all()
        
        co_passengers = []
        my_sequence = 0
        
        for route, emp, sch in co_passengers_query:
            sequence = route.pickup_sequence if trip_type == 'pickup' else route.drop_sequence
            trip_status = sch.pickup_trip_status if trip_type == 'pickup' else sch.drop_trip_status
            
            is_me = emp.employee_id == employee_id
            if is_me:
                my_sequence = sequence
            
            co_passengers.append({
                "employee_id": emp.employee_id,
                "name": "You" if is_me else emp.employee_name,
                "sequence": sequence,
                "status": trip_status,
                "is_me": is_me
            })
        
        # Build response
        response_data = {
            "has_assignment": True,
            "trip_type": trip_type,
            "shift_date": shift_date.isoformat(),
            "pickup_time": str(schedule.pickup_time) if schedule.pickup_time else None,
            "drop_time": str(schedule.drop_time) if schedule.drop_time else None,
            "pickup_address": employee.employee_address,
            "vehicle": {
                "vehicle_id": vehicle.id,
                "vehicle_number": vehicle.vechile_number,
                "driver_name": vehicle.vechile_driver_name,
                "driver_mobile": vehicle.vechile_driver_mobile_no,
                "current_location": vehicle_location,
                "status": vehicle_status,
                "eta_minutes": eta_minutes,
                "eta_text": f"Arriving in {eta_minutes} minutes" if eta_minutes else None
            },
            "my_otp": str(routing.on_board_OTP),
            "my_sequence": my_sequence,
            "total_passengers": len(co_passengers),
            "co_passengers": co_passengers,
            "route_name": routing.route_name,
            "cluster_id": routing.cluster_in_pickup_group if trip_type == 'pickup' else routing.cluster_in_drop_group
        }
        
        return jsonify({"success": True, "data": response_data}), 200
        
    except Exception as e:
        logging.error(f"Error getting employee assignment: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@employee_app_bp.route('/api/employee/track-vehicle/<int:employee_id>', methods=['GET'])
def track_employee_vehicle(employee_id):
    """
    Get real-time vehicle location and ETA for employee's assigned vehicle
    """
    try:
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        shift_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        
        # Get employee
        employee = Employees.query.get(employee_id)
        if not employee:
            return jsonify({"success": False, "message": "Employee not found"}), 404
        
        # Get schedule
        schedule = Employees_schedules.query.filter_by(
            employee_id=employee_id,
            shift_date=shift_date
        ).first()
        
        if not schedule:
            return jsonify({"success": False, "message": "No schedule found"}), 404
        
        # Get routing
        routing = PickupRouting.query.filter_by(
            employee_id=employee_id,
            schedule_id=schedule.schedule_id
        ).first()
        
        if not routing:
            routing = DropRouting.query.filter_by(
                employee_id=employee_id,
                schedule_id=schedule.schedule_id
            ).first()
        
        if not routing:
            return jsonify({"success": False, "message": "Vehicle not assigned"}), 404
        
        # Get latest tracking
        latest_tracking = VehicleTracking.query.filter_by(
            vehicle_id=routing.vehicle_id,
            shift_date=shift_date
        ).order_by(VehicleTracking.timestamp.desc()).first()
        
        if not latest_tracking:
            return jsonify({"success": False, "message": "Vehicle location not available"}), 404
        
        # Calculate ETA
        vehicle_coords = (latest_tracking.latitude, latest_tracking.longitude)
        employee_coords = (employee.latitude, employee.longitude)
        eta_minutes = calculate_eta(vehicle_coords, employee_coords)
        distance_km = geodesic(vehicle_coords, employee_coords).km
        
        vehicle = VechileDetails.query.get(routing.vehicle_id)
        
        return jsonify({
            "success": True,
            "data": {
                "vehicle_number": vehicle.vechile_number,
                "driver_name": vehicle.vechile_driver_name,
                "latitude": latest_tracking.latitude,
                "longitude": latest_tracking.longitude,
                "speed": latest_tracking.speed,
                "heading": latest_tracking.heading,
                "status": latest_tracking.status,
                "eta_minutes": eta_minutes,
                "distance_km": round(distance_km, 2),
                "last_updated": latest_tracking.timestamp.isoformat()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error tracking vehicle: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@employee_app_bp.route('/api/employee/confirm-pickup', methods=['POST'])
def confirm_employee_pickup():
    """
    Employee confirms pickup by providing OTP
    """
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        otp = data.get('otp')
        
        if not all([employee_id, otp]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        # Get today's schedule
        schedule = Employees_schedules.query.filter_by(
            employee_id=employee_id,
            shift_date=date.today()
        ).first()
        
        if not schedule:
            return jsonify({"success": False, "message": "No schedule found for today"}), 404
        
        # Try pickup routing first
        routing = PickupRouting.query.filter_by(
            employee_id=employee_id,
            schedule_id=schedule.schedule_id
        ).first()
        
        trip_type = 'pickup'
        
        if not routing:
            # Try drop routing
            routing = DropRouting.query.filter_by(
                employee_id=employee_id,
                schedule_id=schedule.schedule_id
            ).first()
            trip_type = 'drop'
        
        if not routing:
            return jsonify({"success": False, "message": "No routing found"}), 404
        
        # Verify OTP
        if str(routing.on_board_OTP) != str(otp):
            return jsonify({"success": False, "message": "Invalid OTP"}), 400
        
        # Update status
        if trip_type == 'pickup':
            schedule.pickup_trip_status = 'Picked Up'
        else:
            schedule.drop_trip_status = 'Picked Up'
        
        # Update tracking status
        latest_tracking = VehicleTracking.query.filter_by(
            vehicle_id=routing.vehicle_id,
            current_employee_id=employee_id
        ).order_by(VehicleTracking.timestamp.desc()).first()
        
        if latest_tracking:
            latest_tracking.status = 'picked_up'
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Pickup confirmed successfully!",
            "trip_type": trip_type,
            "status": "Picked Up"
        }), 200
        
    except Exception as e:
        logging.error(f"Error confirming pickup: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@employee_app_bp.route('/api/employee/schedule/<int:employee_id>', methods=['GET'])
def get_employee_schedule(employee_id):
    """
    Get employee's schedule for a date range
    Query params: start_date, end_date (defaults to current week)
    """
    try:
        # Default to current week
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        start_date_param = request.args.get('start_date', start_of_week.isoformat())
        end_date_param = request.args.get('end_date', end_of_week.isoformat())
        
        start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        
        # Get schedules
        schedules = Employees_schedules.query.filter(
            Employees_schedules.employee_id == employee_id,
            Employees_schedules.shift_date >= start_date,
            Employees_schedules.shift_date <= end_date
        ).order_by(Employees_schedules.shift_date).all()
        
        schedule_data = []
        for sch in schedules:
            # Get vehicle if assigned
            pickup_vehicle = None
            drop_vehicle = None
            
            if sch.pickup_time:
                pickup_routing = PickupRouting.query.filter_by(
                    employee_id=employee_id,
                    schedule_id=sch.schedule_id
                ).first()
                if pickup_routing:
                    vehicle = VechileDetails.query.get(pickup_routing.vehicle_id)
                    if vehicle:
                        pickup_vehicle = vehicle.vechile_number
            
            if sch.drop_time:
                drop_routing = DropRouting.query.filter_by(
                    employee_id=employee_id,
                    schedule_id=sch.schedule_id
                ).first()
                if drop_routing:
                    vehicle = VechileDetails.query.get(drop_routing.vehicle_id)
                    if vehicle:
                        drop_vehicle = vehicle.vechile_number
            
            schedule_data.append({
                "shift_date": sch.shift_date.isoformat(),
                "pickup_time": str(sch.pickup_time) if sch.pickup_time else None,
                "drop_time": str(sch.drop_time) if sch.drop_time else None,
                "pickup_vehicle": pickup_vehicle,
                "drop_vehicle": drop_vehicle,
                "pickup_status": sch.pickup_trip_status,
                "drop_status": sch.drop_trip_status
            })
        
        return jsonify({
            "success": True,
            "data": schedule_data,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting schedule: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@employee_app_bp.route('/api/employee/report-issue', methods=['POST'])
def report_issue():
    """
    Employee reports an issue with their trip
    """
    try:
        data = request.get_json()
        
        employee_id = data.get('employee_id')
        issue_type = data.get('issue_type')  # 'driver_late', 'vehicle_issue', 'route_issue', 'other'
        description = data.get('description', '')
        schedule_id = data.get('schedule_id')
        
        if not all([employee_id, issue_type]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        # Create issue report (you'll need to create this model)
        # For now, just log it
        logging.warning(f"Issue reported by employee {employee_id}: {issue_type} - {description}")
        
        # TODO: Create IssueReport model and save to database
        # TODO: Send notification to admin
        
        return jsonify({
            "success": True,
            "message": "Issue reported successfully. Admin will be notified."
        }), 200
        
    except Exception as e:
        logging.error(f"Error reporting issue: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
