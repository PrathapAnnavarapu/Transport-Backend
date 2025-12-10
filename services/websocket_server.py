from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import logging

# Initialize SocketIO
socketio = None

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    @socketio.on('connect')
    def handle_connect():
        logging.info(f"Client connected: {request.sid}")
        emit('connected', {'message': 'Connected to server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logging.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_vehicle_room')
    def handle_join_vehicle(data):
        """Join a room to receive updates for a specific vehicle"""
        vehicle_id = data.get('vehicle_id')
        if vehicle_id:
            room = f"vehicle_{vehicle_id}"
            join_room(room)
            logging.info(f"Client {request.sid} joined room: {room}")
            emit('joined_room', {'room': room, 'vehicle_id': vehicle_id})
    
    @socketio.on('leave_vehicle_room')
    def handle_leave_vehicle(data):
        """Leave a vehicle room"""
        vehicle_id = data.get('vehicle_id')
        if vehicle_id:
            room = f"vehicle_{vehicle_id}"
            leave_room(room)
            logging.info(f"Client {request.sid} left room: {room}")
    
    @socketio.on('join_tracking_room')
    def handle_join_tracking():
        """Join the general tracking room for all vehicles"""
        room = "tracking"
        join_room(room)
        logging.info(f"Client {request.sid} joined tracking room")
        emit('joined_room', {'room': room})
    
    return socketio


def broadcast_vehicle_update(vehicle_id, data):
    """Broadcast vehicle location update to all clients watching this vehicle"""
    if socketio:
        room = f"vehicle_{vehicle_id}"
        socketio.emit('vehicle_location_updated', data, room=room)
        logging.info(f"Broadcasted update for vehicle {vehicle_id} to room {room}")


def broadcast_status_change(vehicle_id, employee_id, status):
    """Broadcast status change (arrived, picked_up, etc)"""
    if socketio:
        room = f"vehicle_{vehicle_id}"
        socketio.emit('status_changed', {
            'vehicle_id': vehicle_id,
            'employee_id': employee_id,
            'status': status
        }, room=room)
        
        # Also broadcast to tracking room
        socketio.emit('status_changed', {
            'vehicle_id': vehicle_id,
            'employee_id': employee_id,
            'status': status
        }, room='tracking')


def broadcast_employee_picked_up(vehicle_id, employee_id, employee_name):
    """Broadcast when an employee is picked up"""
    if socketio:
        room = f"vehicle_{vehicle_id}"
        socketio.emit('employee_picked_up', {
            'vehicle_id': vehicle_id,
            'employee_id': employee_id,
            'employee_name': employee_name
        }, room=room)
