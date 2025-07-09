from Models import db

class DropTripEmployeeLink(db.Model):
    __tablename__ = 'drop_trip_employee_link'

    id = db.Column(db.Integer, primary_key=True)
    drop_routing_id = db.Column(db.Integer, db.ForeignKey('drop_routing.id'))
    drop_trip_billing_id = db.Column(db.Integer, db.ForeignKey('drop_trip_billing.id'))
    employee_id = db.Column(db.String(20), db.ForeignKey('employees.employee_id'))

    # Relationships
    drop_routing = db.relationship('DropRouting', back_populates='drop_trip_links')
    drop_trip_billing = db.relationship('DropTripBilling', back_populates='employees')
    employee = db.relationship('Employees', back_populates='drop_trip_employee_links')




