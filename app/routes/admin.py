# app/routes/admin.py

import os
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.slot import Slot
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask_cors import cross_origin

# Per invio WhatsApp
from twilio.rest import Client  # Assicurati di aver installato 'twilio' con pip

admin_bp = Blueprint('admin', __name__)

# ----------------------------------------------------------------------------
#                              Utility / Helpers
# ----------------------------------------------------------------------------

def send_whatsapp_notification(to_number: str, message: str):
    """
    Esempio di funzione per inviare messaggi WhatsApp via Twilio.
    'to_number' deve essere in formato internazionale con prefisso +, 
    e devi abilitare il sandbox WhatsApp o avere un numero WhatsApp Twilio.
    """
    account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'YOUR_TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'YOUR_TWILIO_AUTH_TOKEN')
    from_whatsapp_number = 'whatsapp:+14155238886'  # Numero di Twilio WhatsApp sandbox o ufficiale
    to_whatsapp_number = f'whatsapp:{to_number}'

    client = Client(account_sid, auth_token)
    try:
        message_obj = client.messages.create(
            body=message,
            from_=from_whatsapp_number,
            to=to_whatsapp_number
        )
        print(f"WhatsApp message sent. SID: {message_obj.sid}")
    except Exception as e:
        print("Errore nell'invio del messaggio WhatsApp:", e)

def admin_only(admin_id, user: User):
    """
    Esempio di check veloce per verificare che 'user' sia un admin e
    che corrisponda all'admin_id.
    """
    if user is None or user.id != admin_id or user.role != 'admin':
        return False
    return True

# ----------------------------------------------------------------------------
#                   Rotta di esempio per invio notifiche WhatsApp
# ----------------------------------------------------------------------------
@admin_bp.route('/notify/whatsapp', methods=['POST'])
@cross_origin()
def notify_whatsapp():
    """
    Esempio di rotta per inviare un messaggio WhatsApp a TUTTI i clienti
    associati a un certo admin, o un messaggio di test.
    Parametri JSON:
    {
      "admin_id": 1,
      "message": "Test message"
    }
    """
    data = request.get_json()
    admin_id = data.get('admin_id')
    message = data.get('message', 'Ciao da Twilio e Flask!')

    # Verifica che l'admin esista
    admin_user = User.query.filter_by(id=admin_id, role='admin').first()
    if not admin_user:
        return jsonify({'error': 'Admin non trovato'}), 404

    # Prendiamo tutti i clienti associati
    clients = User.query.filter_by(admin_id=admin_id, role='client').all()
    
    # Invia a ogni cliente (se ha un numero di telefono valido)
    for client in clients:
        if client.phone:
            send_whatsapp_notification(client.phone, message)
    
    return jsonify({'message': 'WhatsApp inviato a tutti i clienti!'}), 200

# ----------------------------------------------------------------------------
#                          APPOINTMENTS - CRUD
# ----------------------------------------------------------------------------

@admin_bp.route('/appointments/<int:admin_id>', methods=['GET'])
@cross_origin()
def get_appointments(admin_id):
    """
    Ritorna tutti gli appuntamenti relativi agli operatori di uno specifico admin.
    """
    try:
        operator_ids = [op.id for op in User.query.filter_by(admin_id=admin_id, role='operator').all()]
        appointments = Appointment.query.filter(Appointment.operator_id.in_(operator_ids)).all()

        formatted_appointments = []
        for apt in appointments:
            operator = User.query.get(apt.operator_id)
            client = User.query.get(apt.client_id)
            formatted_appointments.append({
                'id': apt.id,
                'start_time': apt.start_time.isoformat(),
                'end_time': apt.end_time.isoformat(),
                'operatorId': operator.id if operator else None,
                'operatorName': operator.username if operator else "N/A",
                'clientName': client.username if client else "N/A",
                'status': apt.status,
                'service_type': apt.service_type
            })
        
        return jsonify({'appointments': formatted_appointments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/appointments', methods=['POST'])
@cross_origin()
def add_appointment():
    """
    Aggiunge un nuovo appuntamento.
    JSON atteso:
    {
      "admin_id": 1,
      "operator_id": 10,
      "client_id": 100,
      "start_time": "2025-01-17T09:00:00",
      "end_time": "2025-01-17T10:00:00",
      "service_type": "Taglio capelli"
    }
    """
    data = request.get_json()
    admin_id = data.get('admin_id')
    
    # Controlliamo che l'admin esista
    admin_user = User.query.filter_by(id=admin_id, role='admin').first()
    if not admin_user:
        return jsonify({'error': 'Admin non valido'}), 403

    # Controlliamo operator e client
    operator = User.query.get(data['operator_id'])
    client = User.query.get(data['client_id'])
    if not operator or operator.admin_id != admin_id or operator.role != 'operator':
        return jsonify({'error': 'Operatore non valido o non di questo admin'}), 400
    if not client or client.role != 'client':
        return jsonify({'error': 'Cliente non valido'}), 400

    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])

        new_appointment = Appointment(
            operator_id=operator.id,
            client_id=client.id,
            start_time=start_time,
            end_time=end_time,
            service_type=data.get('service_type', ''),
            status='pending'
        )

        db.session.add(new_appointment)
        db.session.commit()

        # Eventuale invio di notifica WhatsApp al client
        if client.phone:
            msg = f"Ciao {client.username}, il tuo appuntamento per '{data.get('service_type', '')}' è stato creato il {start_time}."
            send_whatsapp_notification(client.phone, msg)

        return jsonify({
            'message': 'Appuntamento creato con successo',
            'appointment': {
                'id': new_appointment.id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
@cross_origin()
def update_appointment(appointment_id):
    """
    Aggiorna un appuntamento esistente: orario, stato, etc.
    JSON atteso:
    {
      "admin_id": 1,
      "status": "confirmed"
    }
    """
    data = request.get_json()
    admin_id = data.get('admin_id')

    admin_user = User.query.filter_by(id=admin_id, role='admin').first()
    if not admin_user:
        return jsonify({'error': 'Admin non valido'}), 403

    appointment = Appointment.query.get_or_404(appointment_id)
    operator = User.query.get(appointment.operator_id)

    if operator.admin_id != admin_id:
        return jsonify({'error': 'Non autorizzato'}), 403

    try:
        # Aggiorna lo stato se presente
        new_status = data.get('status')
        if new_status:
            appointment.status = new_status
        
        # Esempio: potresti anche aggiornare start_time, end_time, service_type, etc.
        if 'start_time' in data:
            appointment.start_time = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data:
            appointment.end_time = datetime.fromisoformat(data['end_time'])
        if 'service_type' in data:
            appointment.service_type = data['service_type']

        db.session.commit()

        # Eventuale notifica al client del cambio stato
        client = User.query.get(appointment.client_id)
        if client and client.phone and new_status:
            msg = f"Ciao {client.username}, lo stato del tuo appuntamento è ora: {new_status}"
            send_whatsapp_notification(client.phone, msg)

        return jsonify({'message': 'Appuntamento aggiornato con successo'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@cross_origin()
def delete_appointment(appointment_id):
    """
    Elimina un appuntamento.
    JSON atteso:
    {
      "admin_id": 1
    }
    """
    data = request.get_json()
    admin_id = data.get('admin_id')

    appointment = Appointment.query.get_or_404(appointment_id)
    operator = User.query.get(appointment.operator_id)

    if operator.admin_id != admin_id:
        return jsonify({'error': 'Non autorizzato'}), 403

    try:
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({'message': 'Appuntamento eliminato con successo'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ----------------------------------------------------------------------------
#                           OPERATORS - CRUD
# ----------------------------------------------------------------------------

@admin_bp.route('/operators/<int:admin_id>', methods=['GET'])
@cross_origin()
def get_operators(admin_id):
    """
    Ritorna tutti gli operatori di un determinato admin.
    """
    try:
        operators = User.query.filter_by(admin_id=admin_id, role='operator').all()
        return jsonify({
            'operators': [op.to_dict() for op in operators]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/operators/add', methods=['POST'])
@cross_origin()
def add_operator():
    """
    Aggiunge un nuovo operatore all'admin.
    JSON atteso:
    {
      "admin_id": 1,
      "username": "operatore1",
      "email": "op1@example.com",
      "phone": "+39999999999",
      "specialization": "barbiere",
      "password": "segretissimo"
    }
    """
    try:
        data = request.get_json()

        admin_id = data['admin_id']
        admin_user = User.query.filter_by(id=admin_id, role='admin').first()
        if not admin_user:
            return jsonify({'error': 'Admin non valido'}), 403

        # Verifica username / email duplicati
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username già esistente'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email già esistente'}), 400

        new_operator = User(
            username=data['username'],
            email=data['email'],
            phone=data['phone'],
            role='operator',
            admin_id=admin_id,
            specialization=data['specialization'],
            password_hash=generate_password_hash(data['password'])
        )

        db.session.add(new_operator)
        db.session.commit()

        return jsonify({
            'message': 'Operatore aggiunto con successo',
            'operator': new_operator.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/operators/<int:operator_id>', methods=['PUT'])
@cross_origin()
def edit_operator(operator_id):
    """
    Aggiorna i dati di un operatore.
    JSON atteso:
    {
      "admin_id": 1,
      "username": "nuovousername",
      "email": "nuovaemail@example.com",
      "phone": "+3999998888",
      "specialization": "nuova specializzazione"
    }
    """
    try:
        data = request.get_json()
        operator = User.query.get_or_404(operator_id)

        # Controllo che l'operatore appartenga all'admin
        if operator.admin_id != data['admin_id']:
            return jsonify({'error': 'Non autorizzato'}), 403

        # Verifica duplicati
        username_exists = User.query.filter(
            User.username == data['username'],
            User.id != operator_id
        ).first()
        email_exists = User.query.filter(
            User.email == data['email'],
            User.id != operator_id
        ).first()

        if username_exists:
            return jsonify({'error': 'Username già esistente'}), 400
        if email_exists:
            return jsonify({'error': 'Email già esistente'}), 400

        operator.username = data['username']
        operator.email = data['email']
        operator.phone = data['phone']
        operator.specialization = data['specialization']

        db.session.commit()

        return jsonify({
            'message': 'Operatore aggiornato con successo',
            'operator': operator.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/operators/<int:operator_id>', methods=['DELETE'])
@cross_origin()
def delete_operator(operator_id):
    """
    Elimina un operatore e tutti i suoi slot/appuntamenti.
    JSON atteso:
    {
      "admin_id": 1
    }
    """
    try:
        data = request.get_json()
        operator = User.query.get_or_404(operator_id)

        if operator.admin_id != data['admin_id']:
            return jsonify({'error': 'Non autorizzato'}), 403
        
        # Elimina tutti gli slot associati
        Slot.query.filter_by(operator_id=operator_id).delete()
        
        # Elimina tutti gli appuntamenti associati
        Appointment.query.filter_by(operator_id=operator_id).delete()
        
        db.session.delete(operator)
        db.session.commit()
        
        return jsonify({'message': 'Operatore eliminato con successo'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ----------------------------------------------------------------------------
#                            SLOTS - CRUD
# ----------------------------------------------------------------------------

@admin_bp.route('/slots/add', methods=['POST'])
@cross_origin()
def add_slot():
    """
    Aggiunge uno slot (fascia oraria) per un operatore.
    JSON atteso:
    {
      "admin_id": 1,
      "operator_id": 10,
      "start_time": "2025-01-17T09:00:00",
      "end_time": "2025-01-17T12:00:00"
    }
    """
    try:
        data = request.get_json()

        admin_id = data['admin_id']
        admin_user = User.query.filter_by(id=admin_id, role='admin').first()
        if not admin_user:
            return jsonify({'error': 'Admin non valido'}), 403

        operator = User.query.get(data['operator_id'])
        if not operator or operator.admin_id != admin_id:
            return jsonify({'error': 'Operatore non valido o non di questo admin'}), 400

        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))

        # Controllo sovrapposizione slot
        existing_slot = Slot.query.filter(
            Slot.operator_id == data['operator_id'],
            Slot.start_time <= end_time.time(),
            Slot.end_time >= start_time.time()
        ).first()

        if existing_slot:
            return jsonify({'error': 'Esiste già uno slot sovrapposto in questo orario'}), 400

        new_slot = Slot(
            operator_id=data['operator_id'],
            start_time=start_time.time(),
            end_time=end_time.time(),
            day_of_week=start_time.weekday()
        )

        db.session.add(new_slot)
        db.session.commit()

        return jsonify({
            'message': 'Slot aggiunto con successo',
            'slot': new_slot.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/slots/<int:slot_id>', methods=['DELETE'])
@cross_origin()
def delete_slot(slot_id):
    """
    Elimina uno slot.
    JSON atteso:
    {
      "admin_id": 1
    }
    """
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        slot = Slot.query.get_or_404(slot_id)
        operator = User.query.get(slot.operator_id)

        if operator.admin_id != admin_id:
            return jsonify({'error': 'Non autorizzato'}), 403

        db.session.delete(slot)
        db.session.commit()
        return jsonify({'message': 'Slot eliminato con successo'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ----------------------------------------------------------------------------
#                            STATISTICHE
# ----------------------------------------------------------------------------

@admin_bp.route('/stats/<int:admin_id>', methods=['GET'])
@cross_origin()
def get_stats(admin_id):
    """
    Restituisce le statistiche generali sugli appuntamenti
    di tutti gli operatori di un admin.
    Esempio di output:
    {
      "totalAppointments": 12,
      "appointmentStats": [
        { "name": "Pending", "value": 3 },
        { "name": "Confirmed", "value": 5 },
        { "name": "Completed", "value": 2 },
        { "name": "Cancelled", "value": 2 }
      ]
    }
    """
    try:
        operator_ids = [op.id for op in User.query.filter_by(admin_id=admin_id, role='operator').all()]
        
        # Conteggio totale
        total_appointments = Appointment.query.filter(
            Appointment.operator_id.in_(operator_ids)
        ).count()
        
        status_stats = []
        for status in ['pending', 'confirmed', 'completed', 'cancelled']:
            count = Appointment.query.filter(
                Appointment.operator_id.in_(operator_ids),
                Appointment.status == status
            ).count()
            status_stats.append({
                'name': status.capitalize(),
                'value': count
            })

        return jsonify({
            'totalAppointments': total_appointments,
            'appointmentStats': status_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----------------------------------------------------------------------------
#  FINE FILE: admin.py
# ----------------------------------------------------------------------------
