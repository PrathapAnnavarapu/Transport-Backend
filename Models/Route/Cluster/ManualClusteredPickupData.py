from Models import db

class ManualClusteredData(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    shift_date = db.Column(db.Date, nullable=False, index=True)
    data = db.Column(db.JSON, nullable=False)  # Store full pickupTimeGroup dict
