from Models import db
from datetime import datetime


class DropTripBilling(db.Model):
    __tablename__ = 'drop_trip_billing'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vechile_details.id'), nullable=False)
    schedule_id = db.Column(db.Integer, nullable=False)  # ✅ New field
    billing_policy_id = db.Column(db.Integer, db.ForeignKey('billing_policy.id'), nullable=False)

    trip_date = db.Column(db.DateTime, default=datetime.utcnow)
    distance_travelled = db.Column(db.Float, nullable=False)
    fare_amount = db.Column(db.Float, nullable=False)
    billing_mode = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='unpaid')
    route_name = db.Column(db.String(100), nullable=False)

    # Relationships
    vehicle = db.relationship('VechileDetails', back_populates='drop_trip_billings')
    billing_policy = db.relationship('BillingPolicy', back_populates='drop_trip_billings')
    employees = db.relationship('DropTripEmployeeLink', back_populates='drop_trip_billing')






