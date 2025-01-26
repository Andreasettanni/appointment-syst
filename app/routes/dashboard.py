# app/routes/dashboard.py
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.appointment import Appointment, Notification
from app.extensions import db
from datetime import datetime, timedelta

dashboard = Blueprint('dashboard', __name__)

# Admin Dashboard
@dashboard.route('/api/admin/stats', methods=['GET'])
@login_required
def admin_stats():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    # Statistiche di base
    total_operators = len(current_user.operators)
    total_appointments = Appointment.query.join(Appointment.operator)\
        .filter(User.admin_id == current_user.id).count()
    
    # Appuntamenti per operatore
    operator_stats = []
    for operator in current_user.operators:
        appointments = Appointment.query.filter_by(operator_id=operator.id).count()
        operator_stats.append({
            'operator_name': operator.username,
            'appointments_count': appointments
        })

    return jsonify({
        'total_operators': total_operators,
        'total_appointments': total_appointments,
        'operator_stats': operator_stats
    })

# Operator Dashboard
@dashboard.route('/api/operator/appointments', methods=['GET'])
@login_required
def operator_appointments():
    if current_user.role != 'operator':
        return jsonify({'error': 'Unauthorized'}), 403

    start_date = request.args.get('start_date', datetime.now().date().isoformat())
    end_date = request.args.get('end_date', 
                               (datetime.now() + timedelta(days=30)).date().isoformat())

    appointments = Appointment.query\
        .filter_by(operator_id=current_user.id)\
        .filter(Appointment.datetime.between(start_date, end_date))\
        .all()

    return jsonify({
        'appointments': [{
            'id': app.id,
            'datetime': app.datetime.isoformat(),
            'client_name': app.client.username,
            'duration': app.duration,
            'status': app.status
        } for app in appointments]
    })

# Client Dashboard
@dashboard.route('/api/client/appointments', methods=['GET'])
@login_required
def client_appointments():
    if current_user.role != 'client':
        return jsonify({'error': 'Unauthorized'}), 403

    appointments = Appointment.query\
        .filter_by(client_id=current_user.id)\
        .order_by(Appointment.datetime.desc())\
        .all()

    return jsonify({
        'appointments': [{
            'id': app.id,
            'datetime': app.datetime.isoformat(),
            'operator_name': app.operator.username,
            'duration': app.duration,
            'status': app.status
        } for app in appointments]
    })