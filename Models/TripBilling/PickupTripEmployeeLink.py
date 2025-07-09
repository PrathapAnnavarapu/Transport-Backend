from Models import db

class PickupTripEmployeeLink(db.Model):
    __tablename__ = 'pickup_trip_employee_link'

    id = db.Column(db.Integer, primary_key=True)
    pickup_trip_billing_id = db.Column(db.Integer, db.ForeignKey('pickup_trip_billing.id'), nullable=False)
    employee_id = db.Column(db.String(20), db.ForeignKey('employees.employee_id'), nullable=False)
    pickup_routing_id = db.Column(db.Integer, db.ForeignKey('pickup_routing.id'), nullable=True)

    # Relationship back to billing
    pickup_trip_billing = db.relationship('PickupTripBilling', back_populates='employees')

    # Relationship to employee
    employee = db.relationship('Employees', backref='pickup_trip_employee_links')  # Renamed the backref here

    # Relationship to routing entry
    pickup_routing = db.relationship('PickupRouting', back_populates='trip_links')




