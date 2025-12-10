from datetime import datetime
from Models import db

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'employee', 'admin', 'driver'
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), default='info')  # 'info', 'alert', 'success', 'warning'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Notification {self.id} for {self.user_type} {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_type': self.user_type,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }


class IssueReport(db.Model):
    __tablename__ = 'issue_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.employee_id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('employees_schedules.schedule_id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vechile_details.id'))
    
    issue_type = db.Column(db.String(50), nullable=False)  # 'driver_late', 'vehicle_issue', 'route_issue', 'other'
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # 'open', 'in_progress', 'resolved', 'closed'
    priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer)  # Admin user ID who resolved
    resolution_notes = db.Column(db.Text)
    
    # Relationships
    employee = db.relationship('Employees', backref='issue_reports', lazy=True)
    schedule = db.relationship('Employees_schedules', foreign_keys=[schedule_id], lazy=True)
    vehicle = db.relationship('VechileDetails', foreign_keys=[vehicle_id], lazy=True)
    
    def __repr__(self):
        return f'<IssueReport {self.id} - {self.issue_type} by Employee {self.employee_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.employee_name if self.employee else None,
            'schedule_id': self.schedule_id,
            'vehicle_id': self.vehicle_id,
            'vehicle_number': self.vehicle.vechile_number if  self.vehicle else None,
            'issue_type': self.issue_type,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes
        }
