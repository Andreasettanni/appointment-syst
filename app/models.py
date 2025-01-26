from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum('admin', 'operator', 'client'), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Operator(db.Model):
    __tablename__ = 'operators'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    specialization = db.Column(db.String(100))
    
    user = db.relationship('User', foreign_keys=[id])
    admin = db.relationship('User', foreign_keys=[admin_id])

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    operator_id = db.Column(db.Integer, db.ForeignKey('operators.id'))
    date_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('pending', 'confirmed', 'cancelled'), default='pending')
    notes = db.Column(db.Text)
    
    client = db.relationship('User', foreign_keys=[client_id])
    operator = db.relationship('Operator', foreign_keys=[operator_id])
