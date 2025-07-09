from Models import db
from datetime import datetime
from sqlalchemy import Time

from Models import db
from datetime import datetime
from sqlalchemy import Time

class DropRouting(db.Model):
    __tablename__ = 'drop_routing'  # Optional: Ensure you define the table name (not necessary if it's the same as the class)

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.String(20), db.ForeignKey('employees.employee_id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('employees_schedules.schedule_id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vechile_details.id'), nullable=False)

    drop_sequence = db.Column(db.Integer, nullable=False)
    distance_from_last = db.Column(db.Float, nullable=False)
    cumulative_distance = db.Column(db.Float, nullable=False)
    calculated_drop_time = db.Column(Time, nullable=False)
    drop_timing_group = db.Column(Time, nullable=False)
    cluster_in_drop_group = db.Column(db.String(255), nullable=False)
    route_name = db.Column(db.String(100), nullable=False)
    route_distance = db.Column(db.Integer, nullable=False)
    on_board_OTP = db.Column(db.Integer, nullable=False)  # New column
    off_board_OTP = db.Column(db.Integer, nullable=False)  # New column
    drop_vehicle_assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    on_board_OTP_entered_at = db.Column(db.DateTime, nullable=True)
    off_board_OTP_entered_at = db.Column(db.DateTime, nullable=True)
    OTP_entered_by = db.Column(db.String(255), nullable=True)

    # In DropRouting model, Relationships
    employee = db.relationship('Employees', back_populates='drop_routings', lazy=True)
    schedule = db.relationship('Employees_schedules', backref='drop_routing_data', lazy=True)
    vehicle = db.relationship('VechileDetails', backref='drop_routing_data', lazy=True)

    # Correcting the redundant relationships
    # Keep only one relationship to DropTripEmployeeLink
    drop_trip_links = db.relationship('DropTripEmployeeLink', back_populates='drop_routing')

    # Relationship with DropTripBilling through DropTripEmployeeLink (many-to-many)
    trip_billings = db.relationship(
        'DropTripBilling',
        secondary='drop_trip_employee_link',
        primaryjoin='DropRouting.id == DropTripEmployeeLink.drop_routing_id',
        secondaryjoin='DropTripBilling.id == DropTripEmployeeLink.drop_trip_billing_id',
        viewonly=True
    )




