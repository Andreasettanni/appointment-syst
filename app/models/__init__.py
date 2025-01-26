# app/models/__init__.py
from app.models.user import User
from app.models.appointment import Appointment
from app.models.slot import Slot

__all__ = ['User', 'Appointment', 'Slot']