from Models import db
from datetime import datetime
from sqlalchemy import Time

class PickupRouting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), db.ForeignKey('employees.employee_id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('employees_schedules.schedule_id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vechile_details.id'), nullable=False)


    pickup_sequence = db.Column(db.Integer, nullable=False)
    distance_from_last = db.Column(db.Float, nullable=False)
    cumulative_distance = db.Column(db.Float, nullable=False)
    calculated_pickup_time = db.Column(Time, nullable=False)
    pickup_timing_group = db.Column(Time, nullable=False)
    cluster_in_pickup_group = db.Column(db.String(255), nullable=False)
    route_name = db.Column(db.String(100), nullable=True)
    route_distance= db.Column(db.Integer, nullable=False)
    on_board_OTP = db.Column(db.Integer, nullable=False)
    off_board_OTP = db.Column(db.Integer, nullable=False)
    pickup_vehicle_assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    on_board_OTP_entered_at = db.Column(db.DateTime, nullable=True)
    off_board_OTP_entered_at = db.Column(db.DateTime, nullable=True)
    OTP_entered_by= db.Column(db.String(255), nullable=True)


    employee = db.relationship('Employees', back_populates='pickup_routings', lazy=True)
    schedule = db.relationship('Employees_schedules', backref='pickup_routing_data', lazy=True)
    vehicle = db.relationship('VechileDetails', backref='pickup_routing_data', lazy=True)
    trip_links = db.relationship('PickupTripEmployeeLink', back_populates='pickup_routing')

    trip_billings = db.relationship(
        'PickupTripBilling',
        secondary='pickup_trip_employee_link',
        primaryjoin='PickupRouting.id == PickupTripEmployeeLink.pickup_routing_id',
        secondaryjoin='PickupTripBilling.id == PickupTripEmployeeLink.pickup_trip_billing_id',
        viewonly=True
    )




