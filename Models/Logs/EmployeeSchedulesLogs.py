
from Models import db

class EmployeeScheduleLogs(db.Model):
    __tablename__ = 'employee_schedule_logs'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('employees_schedules.schedule_id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # e.g., 'created', 'updated', 'deleted'
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    created_by_id = db.Column(db.String(50), nullable=False)
    created_by_name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)  # Optional details or JSON of changes
    schedule = db.relationship('Employees_schedules', back_populates='logs')
