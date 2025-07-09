from Models import db


class Employees_available_schedules(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pickup_time = db.Column(db.Time, unique=True, nullable=True)
    drop_time = db.Column(db.Time, unique=True, nullable=True)

