# app/models/operator.py
from app.extensions import db

class Operator(db.Model):
    __tablename__ = 'operators'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    specialization = db.Column(db.String(100))

    # Relazioni
    user = db.relationship('User', foreign_keys=[id])
    admin = db.relationship('User', foreign_keys=[admin_id])