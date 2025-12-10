from datetime import datetime
from Models import db

class VehicleTracking(db.Model):
    __tablename__ = 'vehicle_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vechile_details.id'), nullable=False)
    
    # Location data
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float)  # km/h
    heading = db.Column(db.Float)  # degrees (0-360)
    accuracy = db.Column(db.Float)  # meters
    
    # Route info
    route_id = db.Column(db.Integer)  # Can be pickup or drop routing ID
    cluster_id = db.Column(db.String(50))
    pickup_time_group = db.Column(db.String(20))
    trip_type = db.Column(db.String(20))  # 'pickup' or 'drop'
    shift_date = db.Column(db.Date)
    
    # Status tracking
    status = db.Column(db.String(50), default='idle')  # 'idle', 'en_route', 'arrived', 'picked_up', 'completed'
    current_employee_id = db.Column(db.Integer, db.ForeignKey('employees.employee_id'))
    current_employee_index = db.Column(db.Integer, default=0)  # Position in sequence
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = db.relationship('VechileDetails', backref='tracking_history', lazy=True)
    current_employee = db.relationship('Employees', foreign_keys=[current_employee_id], lazy=True)
    
    def __repr__(self):
        return f'<VehicleTracking {self.vehicle_id} at ({self.latitude}, {self.longitude})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'speed': self.speed,
            'heading': self.heading,
            'accuracy': self.accuracy,
            'route_id': self.route_id,
            'cluster_id': self.cluster_id,
            'pickup_time_group': self.pickup_time_group,
            'trip_type': self.trip_type,
            'shift_date': self.shift_date.isoformat() if self.shift_date else None,
            'status': self.status,
            'current_employee_id': self.current_employee_id,
            'current_employee_index': self.current_employee_index,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
