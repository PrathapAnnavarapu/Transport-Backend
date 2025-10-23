from Models import db

class Locations(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    location_name = db.Column(db.String(150), nullable=False, unique=True)   # Hyderabad, Bangalore, etc.
    location_code = db.Column(db.String(50), nullable=True, unique=True)     # Optional short code like HYD, BLR
    address = db.Column(db.String(255), nullable=True)                       # Optional full address
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True, default="India")
    is_active = db.Column(db.Boolean, default=True)

    # 🔗 Relationships
    # employees = db.relationship("Employees", back_populates="location", lazy="select")
    # schedules = db.relationship("Employees_schedules", back_populates="location", lazy="select")

    def __repr__(self):
        return f"<Location {self.location_name} ({self.id})>"
