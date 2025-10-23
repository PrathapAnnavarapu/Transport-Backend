from Models import db

class Employees_schedules(db.Model):
    __tablename__ = "employees_schedules"

    schedule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.String(20), db.ForeignKey('employees.employee_id'), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    pickup_time = db.Column(db.Time, nullable=True)
    drop_time = db.Column(db.Time, nullable=True)
    pickup_trip_status = db.Column(db.String(200), nullable=True)
    drop_trip_status = db.Column(db.String(200), nullable=True)
    employee = db.relationship('Employees', back_populates='schedules')
    logs = db.relationship('EmployeeScheduleLogs', back_populates='schedule', lazy='select')