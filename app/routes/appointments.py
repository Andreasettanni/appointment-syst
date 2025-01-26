from flask import Blueprint, request, jsonify
from app.models import Appointment
from app import db

bp = Blueprint('appointments', __name__, url_prefix='/api/appointments')

@bp.route('/', methods=['GET'])
def get_appointments():
    appointments = Appointment.query.all()
    return jsonify([{
        'id': a.id,
        'client_id': a.client_id,
        'operator_id': a.operator_id,
        'date_time': a.date_time.isoformat(),
        'duration': a.duration,
        'status': a.status
    } for a in appointments]), 200

@bp.route('/', methods=['POST'])
def create_appointment():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('client_id', 'operator_id', 'date_time', 'duration')):
        return jsonify({'error': 'Missing required fields'}), 400
        
    appointment = Appointment(
        client_id=data['client_id'],
        operator_id=data['operator_id'],
        date_time=data['date_time'],
        duration=data['duration'],
        notes=data.get('notes', '')
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({'message': 'Appointment created successfully'}), 201

@bp.route('/<int:id>', methods=['PUT'])
def update_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    data = request.get_json()
    
    if 'status' in data:
        appointment.status = data['status']
    if 'notes' in data:
        appointment.notes = data['notes']
        
    db.session.commit()
    
    return jsonify({'message': 'Appointment updated successfully'}), 200