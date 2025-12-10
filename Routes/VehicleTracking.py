from flask import Blueprint, request, jsonify
from Models import db
from Models.VehicleTracking.VehicleTracking import VehicleTracking
from Models.Vechile.VechileDetails import VechileDetails
from Models.Employee.Employees import Employees
from Models.Route.PickupRouting import PickupRouting
from Models.Route.DropRouting import DropRouting
from Models.Schedules.Employees_schedules import Employees_schedules
from datetime import datetime, date
from sqlalchemy import and_, func
from geopy.distance import geodesic
import logging

# Import WebSocket broadcaster
from services.websocket_server import broadcast_vehicle_update, broadcast_status_change, broadcast_employee_picked_up
from services.notification_service import notification_service

vehicle_tracking_bp = Blueprint('vehicle_tracking', __name__)

# Proximity threshold in meters (e.g., 100 meters = vehicle has "arrived")
PROXIMITY_THRESHOLD_METERS = 100

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in meters"""
    return geodesic((lat1, lon1), (lat2, lon2)).meters


@vehicle_tracking_bp.route('/api/vehicle/tracking/update', methods=['POST'])
def update_vehicle_location():
    """
    Update vehicle location and automatically handle status updates based on proximity
    Request Body:
    {
        "vehicle_id": 123,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "speed": 45.5,
        "heading": 180,
        "accuracy": 10,
        "route_id": 456,
        "cluster_id": "cluster1",
        "pickup_time_group": "08:00",
        "trip_type": "pickup",
        "shift_date": "2025-12-10"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'vehicle_id' not in data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        vehicle_id = data['vehicle_id']
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        trip_type = data.get('trip_type', 'pickup')
        route_id = data.get('route_id')
        shift_date_str = data.get('shift_date')
        
        # Parse shift date
        shift_date = datetime.strptime(shift_date_str, '%Y-%m-%d').date() if shift_date_str else date.today()
        
        # Get current route details and employee sequence
        current_employee_id = None
        current_employee_index = 0
        status = 'en_route'
        next_employee_coords = None
        
        if route_id:
            # Get route details based on trip type
            if trip_type == 'pickup':
                route_query = PickupRouting.query.filter_by(
                    vehicle_id=vehicle_id,
                    cluster_in_pickup_group=data.get('cluster_id')
                ).join(Employees_schedules, PickupRouting.schedule_id == Employees_schedules.schedule_id)\
                 .filter(Employees_schedules.shift_date == shift_date)\
                 .order_by(PickupRouting.pickup_sequence).all()
            else:  # drop
                route_query = DropRouting.query.filter_by(
                    vehicle_id=vehicle_id,
                    cluster_in_drop_group=data.get('cluster_id')
                ).join(Employees_schedules, DropRouting.schedule_id == Employees_schedules.schedule_id)\
                 .filter(Employees_schedules.shift_date == shift_date)\
                 .order_by(DropRouting.drop_sequence).all()
            
            if route_query:
                # Find next employee to pick up (not yet picked up)
                for idx, routing in enumerate(route_query):
                    schedule = routing.pickup_schedule if trip_type == 'pickup' else routing.drop_schedule
                    trip_status = schedule.pickup_trip_status if trip_type == 'pickup' else schedule.drop_trip_status
                    
                    if trip_status not in ['Picked Up', 'Completed']:
                        current_employee_id = routing.employee_id
                        current_employee_index = idx
                        
                        # Get employee coordinates
                        employee = Employees.query.get(current_employee_id)
                        if employee:
                            next_employee_coords = (employee.latitude, employee.longitude)
                        break
        
        # Check proximity to next employee
        if next_employee_coords:
            distance_to_employee = calculate_distance(
                latitude, longitude,
                next_employee_coords[0], next_employee_coords[1]
            )
            
            logging.info(f"Vehicle {vehicle_id} is {distance_to_employee:.2f}m from employee {current_employee_id}")
            
           # Update status to "arrived" if within threshold
            if distance_to_employee <= PROXIMITY_THRESHOLD_METERS:
                status = 'arrived'
                logging.info(f"Vehicle {vehicle_id} has ARRIVED at employee {current_employee_id}")
        
        # Create tracking record
        tracking = VehicleTracking(
            vehicle_id=vehicle_id,
            latitude=latitude,
            longitude=longitude,
            speed=data.get('speed'),
            heading=data.get('heading'),
            accuracy=data.get('accuracy'),
            route_id=route_id,
            cluster_id=data.get('cluster_id'),
            pickup_time_group=data.get('pickup_time_group'),
            trip_type=trip_type,
            shift_date=shift_date,
            status=status,
            current_employee_id=current_employee_id,
            current_employee_index=current_employee_index,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(tracking)
        db.session.commit()
        
        # Broadcast real-time update via WebSocket
        broadcast_data = {
            'vehicle_id': vehicle_id,
            'latitude': latitude,
            'longitude': longitude,
            'speed': tracking.speed,
            'status': status,
            'current_employee_id': current_employee_id,
            'eta_minutes':distance_to_employee if next_employee_coords else None,
            'timestamp': tracking.timestamp.isoformat()
        }
        broadcast_vehicle_update(vehicle_id, broadcast_data)
        
        # Send SMS notification if status changed to arrived
        if status == 'arrived' and current_employee_id:
            employee = Employees.query.get(current_employee_id)
            if employee and employee.employee_mobile_no:
                routing_temp = PickupRouting.query.filter_by(employee_id=current_employee_id).first()
                if not routing_temp:
                    routing_temp = DropRouting.query.filter_by(employee_id=current_employee_id).first()
                if routing_temp:
                    vehicle = VechileDetails.query.get(vehicle_id)
                    notification_service.send_vehicle_arrived_sms(
                        employee.employee_mobile_no,
                        vehicle.vechile_number if vehicle else str(vehicle_id),
                        routing_temp.on_board_OTP
                    )
        
        return jsonify({
            "success": True,
            "message": "Location updated successfully",
            "tracking_id": tracking.id,
            "status": status,
            "distance_to_next_employee": distance_to_employee if next_employee_coords else None,
            "current_employee_id": current_employee_id
        }), 200
        
    except Exception as e:
        logging.error(f"Error updating vehicle location: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@vehicle_tracking_bp.route('/api/vehicle/tracking/verify-otp', methods=['POST'])
def verify_pickup_otp():
    """
    Verify OTP and update status to picked_up
    Request Body:
    {
        "employee_id": 123,
        "schedule_id": 456,
        "otp": "1234",
        "trip_type": "pickup"
    }
    """
    try:
        data = request.get_json()
        
        employee_id = data.get('employee_id')
        schedule_id = data.get('schedule_id')
        otp = data.get('otp')
        trip_type = data.get('trip_type', 'pickup')
        
        if not all([employee_id, schedule_id, otp]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        # Get routing record
        if trip_type == 'pickup':
            routing = PickupRouting.query.filter_by(
                employee_id=employee_id,
                schedule_id=schedule_id
            ).first()
        else:
            routing = DropRouting.query.filter_by(
                employee_id=employee_id,
                schedule_id=schedule_id
            ).first()
        
        if not routing:
            return jsonify({"success": False, "message": "Routing record not found"}), 404
        
        # Verify OTP
        expected_otp = str(routing.on_board_OTP)
        if str(otp) != expected_otp:
            return jsonify({"success": False, "message": "Invalid OTP"}), 400
        
        # Update schedule status to "Picked Up"
        schedule = Employees_schedules.query.get(schedule_id)
        if schedule:
            if trip_type == 'pickup':
                schedule.pickup_trip_status = 'Picked Up'
            else:
                schedule.drop_trip_status = 'Picked Up'
            
            # Update vehicle tracking status
            latest_tracking = VehicleTracking.query.filter_by(
                vehicle_id=routing.vehicle_id,
                current_employee_id=employee_id
            ).order_by(VehicleTracking.timestamp.desc()).first()
            
            if latest_tracking:
                latest_tracking.status = 'picked_up'
            
            db.session.commit()
            
            # Broadcast WebSocket event
            broadcast_employee_picked_up(routing.vehicle_id, employee_id, employee.employee_name if employee else str(employee_id))
            broadcast_status_change(routing.vehicle_id, employee_id, 'picked_up')
            
            # Send SMS notification
            if employee and employee.employee_mobile_no:
                notification_service.send_trip_started_sms(
                    employee.employee_mobile_no,
                    "Office" if trip_type == 'pickup' else "Home"
                )
            
            return jsonify({
                "success": True,
                "message": "OTP verified successfully. Employee picked up.",
                "employee_id": employee_id,
                "status": "Picked Up"
            }), 200
        else:
            return jsonify({"success": False, "message": "Schedule not found"}), 404
            
    except Exception as e:
        logging.error(f"Error verifying OTP: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@vehicle_tracking_bp.route('/api/vehicle/tracking/current', methods=['GET'])
def get_current_vehicle_locations():
    """
    Get current location of all active vehicles
    Query params:
    - date: YYYY-MM-DD (optional, defaults to today)
    - trip_type: 'pickup' or 'drop' (optional)
    - status: 'en_route', 'arrived', 'picked_up', etc (optional)
    """
    try:
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        trip_type = request.args.get('trip_type')
        status_filter = request.args.get('status')
        
        shift_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        
        # Get latest location for each active vehicle
        subquery = db.session.query(
            VehicleTracking.vehicle_id,
            func.max(VehicleTracking.timestamp).label('latest_time')
        ).filter(
            VehicleTracking.shift_date == shift_date
        ).group_by(VehicleTracking.vehicle_id).subquery()
        
        query = db.session.query(VehicleTracking).join(
            subquery,
            and_(
                VehicleTracking.vehicle_id == subquery.c.vehicle_id,
                VehicleTracking.timestamp == subquery.c.latest_time
            )
        ).join(VechileDetails, VehicleTracking.vehicle_id == VechileDetails.id)
        
        if trip_type:
            query = query.filter(VehicleTracking.trip_type == trip_type)
        if status_filter:
            query = query.filter(VehicleTracking.status == status_filter)
        
        vehicles = query.all()
        
        result = []
        for track in vehicles:
            employee_name = None
            if track.current_employee_id:
                employee = Employees.query.get(track.current_employee_id)
                employee_name = employee.employee_name if employee else None
            
            result.append({
                "vehicle_id": track.vehicle_id,
                "vehicle_number": track.vehicle.vechile_number,
                "vehicle_owner": track.vehicle.vechile_owner_name,
                "latitude": track.latitude,
                "longitude": track.longitude,
                "speed": track.speed,
                "heading": track.heading,
                "route_id": track.route_id,
                "cluster_id": track.cluster_id,
                "pickup_time_group": track.pickup_time_group,
                "trip_type": track.trip_type,
                "status": track.status,
                "current_employee_id": track.current_employee_id,
                "current_employee_name": employee_name,
                "current_employee_index": track.current_employee_index,
                "last_updated": track.timestamp.isoformat()
            })
        
        return jsonify({"success": True, "data": result}), 200
        
    except Exception as e:
        logging.error(f"Error fetching vehicle locations: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@vehicle_tracking_bp.route('/api/vehicle/tracking/route/<cluster_id>', methods=['GET'])
def get_route_tracking(cluster_id):
    """
    Get vehicle tracking and employee details for a specific cluster
    Query params:
    - trip_type: 'pickup' or 'drop'
    - date: YYYY-MM-DD
    - pickup_time: HH:MM (for pickup) or drop_time: HH:MM (for drop)
    """
    try:
        trip_type = request.args.get('trip_type', 'pickup')
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        time_param = request.args.get('pickup_time' if trip_type == 'pickup' else 'drop_time')
        
        shift_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        
        # Get latest tracking for this cluster
        latest_tracking = VehicleTracking.query.filter_by(
            cluster_id=cluster_id,
            trip_type=trip_type,
            shift_date=shift_date
        ).order_by(VehicleTracking.timestamp.desc()).first()
        
        if not latest_tracking:
            return jsonify({"success": False, "message": "No tracking data found"}), 404
        
        # Get route details with employees
        if trip_type == 'pickup':
            route_details = db.session.query(PickupRouting, Employees, Employees_schedules).join(
                Employees, PickupRouting.employee_id == Employees.employee_id
            ).join(
                Employees_schedules, PickupRouting.schedule_id == Employees_schedules.schedule_id
            ).filter(
                PickupRouting.cluster_in_pickup_group == cluster_id,
                PickupRouting.vehicle_id == latest_tracking.vehicle_id,
                Employees_schedules.shift_date == shift_date
            ).order_by(PickupRouting.pickup_sequence).all()
        else:
            route_details = db.session.query(DropRouting, Employees, Employees_schedules).join(
                Employees, DropRouting.employee_id == Employees.employee_id
            ).join(
                Employees_schedules, DropRouting.schedule_id == Employees_schedules.schedule_id
            ).filter(
                DropRouting.cluster_in_drop_group == cluster_id,
                DropRouting.vehicle_id == latest_tracking.vehicle_id,
                Employees_schedules.shift_date == shift_date
            ).order_by(DropRouting.drop_sequence).all()
        
        employees = []
        for routing, employee, schedule in route_details:
            trip_status = schedule.pickup_trip_status if trip_type == 'pickup' else schedule.drop_trip_status
            sequence = routing.pickup_sequence if trip_type == 'pickup' else routing.drop_sequence
            
            employees.append({
                "employee_id": employee.employee_id,
                "employee_name": employee.employee_name,
                "employee_address": employee.employee_address,
                "latitude": employee.latitude,
                "longitude": employee.longitude,
                "sequence": sequence,
                "trip_status": trip_status,
                "is_current": employee.employee_id == latest_tracking.current_employee_id
            })
        
        vehicle = VechileDetails.query.get(latest_tracking.vehicle_id)
        
        return jsonify({
            "success": True,
            "vehicle": {
                "vehicle_id": latest_tracking.vehicle_id,
                "vehicle_number": vehicle.vechile_number if vehicle else None,
                "vehicle_owner": vehicle.vechile_owner_name if vehicle else None,
                "latitude": latest_tracking.latitude,
                "longitude": latest_tracking.longitude,
                "speed": latest_tracking.speed,
                "status": latest_tracking.status,
                "last_updated": latest_tracking.timestamp.isoformat()
            },
            "employees": employees,
            "current_employee_index": latest_tracking.current_employee_index,
            "cluster_id": cluster_id,
            "trip_type": trip_type
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching route tracking: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
