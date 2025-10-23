from Models import db
from datetime import datetime
from sqlalchemy import Time
from sqlalchemy import JSON



class Spocs(db.Model):
    __tablename__ = 'spocs'

    id = db.Column(db.Integer, primary_key=True)
    spocData = db.Column(JSON)



