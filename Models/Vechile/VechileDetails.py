from Models import db
from datetime import datetime

class VechileDetails(db.Model):
    __tablename__ = 'vechile_details'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    billing_policy_id = db.Column(db.Integer, db.ForeignKey('billing_policy.id'))

    vechile_number = db.Column(db.String(100), unique=True, nullable=False)
    vendor_type = db.Column(db.String(50))
    vendor_name = db.Column(db.String(100))
    vechile_owner_name = db.Column(db.String(100))
    vechile_driver_name = db.Column(db.String(100))
    vechile_name = db.Column(db.String(100))
    vechile_model = db.Column(db.String(100))
    vechile_owner_mobile_no = db.Column(db.String(15))
    vechile_driver_mobile_no = db.Column(db.String(15))
    vechile_owner_address = db.Column(db.String(100))
    vechile_driver_address = db.Column(db.String(100))
    billing_mode = db.Column(db.String(100))

    # Relationships
    pickup_trip_billings = db.relationship('PickupTripBilling', back_populates='vehicle', lazy='dynamic')
    drop_trip_billings = db.relationship('DropTripBilling', back_populates='vehicle', lazy='dynamic')
    billing_policy = db.relationship('BillingPolicy', back_populates='vehicles', foreign_keys=[billing_policy_id],lazy='joined')




