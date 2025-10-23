from Models import db
from datetime import datetime
from sqlalchemy import Time


class Employees(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(120), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    employee_address = db.Column(db.String(1020), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    home_area=db.Column(db.String(200), nullable=False)
    active_status = db.Column(db.String(200), nullable=False)
    employee_mobile_no = db.Column(db.BigInteger, unique=True, nullable=False)
    employee_email = db.Column(db.String(120), unique=True, nullable=False)
    process = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=True)  # Consider hashing in logic
    role = db.Column(db.String(100), nullable=False)
    work_location = db.Column(db.String(100), nullable=False)
    poc_name = db.Column(db.String(120), nullable=True)
    poc_mobile_no = db.Column(db.BigInteger, nullable=True)

    employee_created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    schedules = db.relationship(
        'Employees_schedules',
        back_populates='employee',
        cascade="all, delete-orphan",
        lazy='joined'
    )

    pickup_routings = db.relationship(
        'PickupRouting',
        back_populates='employee',
        cascade="all, delete-orphan",
        lazy='select'
    )

    drop_routings = db.relationship(
        'DropRouting',
        back_populates='employee',
        cascade="all, delete-orphan",
        lazy='select'
    )

    drop_routing_data = db.relationship(  # Optional: If it's a different use case
        'DropRouting',
        back_populates='employee',
        viewonly=True,  # Prevents conflicts if it's redundant
        lazy='noload'
    )

    drop_trip_employee_links = db.relationship('DropTripEmployeeLink', back_populates='employee')
    pickup_trip_links = db.relationship('PickupTripEmployeeLink', back_populates='employee')  # Keep this intact


