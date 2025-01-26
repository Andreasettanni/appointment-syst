# app/models/user.py
from app.models.base import db, datetime
from app.models.appointment import Appointment
from app.models.slot import Slot

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    specialization = db.Column(db.String(100))

    # Relazioni
    operators = db.relationship('User', 
                              backref=db.backref('admin', remote_side=[id]),
                              foreign_keys=[admin_id])
                              
    appointments_as_operator = db.relationship('Appointment',
                                            backref='operator',
                                            foreign_keys='Appointment.operator_id',
                                            lazy='dynamic')
                                            
    appointments_as_client = db.relationship('Appointment',
                                          backref='client',
                                          foreign_keys='Appointment.client_id',
                                          lazy='dynamic')
                                          
    slots = db.relationship('Slot', 
                           backref='operator',
                           lazy='dynamic')