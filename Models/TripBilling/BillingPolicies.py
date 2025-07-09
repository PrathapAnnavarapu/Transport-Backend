from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from Models import db

class BillingPolicy(db.Model):
    __tablename__ = 'billing_policy'

    id = db.Column(db.Integer, primary_key=True)
    billing_mode = db.Column(db.String(50), nullable=False)

    # Relationship: One-to-many with VechileDetails
    vehicles = db.relationship(
        'VechileDetails',
        back_populates='billing_policy',
        foreign_keys='VechileDetails.billing_policy_id'  # Ensure this is the correct foreign key
    )

    # Fare structure
    base_fare = db.Column(db.Float, default=0.0)
    rate_per_km = db.Column(db.Float, default=0.0)
    rate_per_min = db.Column(db.Float, default=0.0)
    night_surcharge_multiplier = db.Column(db.Float, default=1.0)

    # Subscription structure
    plan_name = db.Column(db.String(100), nullable=True)
    monthly_fee = db.Column(db.Float, default=0.0)
    included_rides = db.Column(db.Integer, default=0)
    extra_ride_price = db.Column(db.Float, default=0.0)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with Zone: One-to-many
    zones = db.relationship('Zone', backref='policy', cascade='all, delete-orphan', lazy=True)

    pickup_trip_billings = db.relationship('PickupTripBilling', back_populates='billing_policy')
    drop_trip_billings = db.relationship('DropTripBilling', back_populates='billing_policy')



class Zone(db.Model):
    __tablename__ = 'zone'

    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(100))
    distance_min = db.Column(db.Float, default=0.0)
    distance_max = db.Column(db.Float, default=0.0)
    fixed_price = db.Column(db.Float, default=0.0)

    billing_policy_id = db.Column(db.Integer, db.ForeignKey('billing_policy.id'), nullable=False)



