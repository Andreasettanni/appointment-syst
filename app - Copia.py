from flask import Flask, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import pymysql
from twilio.rest import Client

pymysql.install_as_MySQLdb()

# Sostituisci la configurazione CORS esistente con questa:

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True,  # Importante per le richieste con credenziali
        "expose_headers": ["Content-Range", "X-Content-Range"]
    }
})

# Aggiungi questo decorator per gestire tutte le risposte
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Configurazione Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/appointment_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'chiave_super_segreta_123'

db = SQLAlchemy(app)

# Configurazione Twilio per WhatsApp
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'your_account_sid')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token')
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'  # Numero Twilio WhatsApp





# Modelli
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
    specialization = db.Column(db.String(100), nullable=True)

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, nullable=False)  # in minuti
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    service_type = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Slot(db.Model):
    __tablename__ = 'slots'
    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 per Lun-Dom
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Crea tutte le tabelle
with app.app_context():
    db.create_all()

# Utility function per WhatsApp
def send_whatsapp_notification(to_number, message):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{to_number}'
        )
        print(f"WhatsApp inviato: {message.sid}")
        return True
    except Exception as e:
        print(f"Errore invio WhatsApp: {str(e)}")
        return False

# Routes principali per reindirizzamento a React
@app.route('/')
def index():
    return redirect('http://localhost:3000')

@app.route('/admin/dashboard')
def admin_dashboard():
    return redirect('http://localhost:3000/admin/dashboard')

# API Auth
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validazione
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username già esistente'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email già esistente'}), 400

    # Hash password e crea utente
    hashed_password = generate_password_hash(data['password'], method='scrypt')
    new_user = User(
        username=data['username'],
        password_hash=hashed_password,
        email=data['email'],
        phone=data.get('phone', ''),
        role=data.get('role', 'client')
    )
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'Registrazione completata',
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'role': new_user.role
        }
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'admin_id': user.admin_id,
                'phone': user.phone
            }
        }), 200
    
    return jsonify({'error': 'Credenziali non valide'}), 401

@app.route("/api/calendar/<int:user_id>", methods=["GET"])
def get_calendar_data(user_id):
    user = User.query.get_or_404(user_id)

    # Prepara la lista di "events"
    events = []

    # Se user è admin, prendi TUTTI gli slot e TUTTI gli appuntamenti
    if user.role == "admin":
        slots = Slot.query.filter_by(is_active=True).all()
        appointments = Appointment.query.all()
    elif user.role == "operator":
        # Solo slot di quell'operatore
        slots = Slot.query.filter_by(operator_id=user.id, is_active=True).all()
        # Appuntamenti di quell'operatore
        appointments = Appointment.query.filter_by(operator_id=user.id).all()
    else:
        # client
        # prendi TUTTI gli slot (così può prenotare chi vuole)
        slots = Slot.query.filter_by(is_active=True).all()
        # prendi solo i suoi appuntamenti
        appointments = Appointment.query.filter_by(client_id=user.id).all()

    # 1) converto slot in "event" => generazione date (solo prossima ricorrenza)
    for slot in slots:
        # Calcolo la data base (prossimo day_of_week)
        # es. se slot.day_of_week=1 (lun) e oggi è mercoledì, lo sposta al prossimo lunedì
        now = datetime.now()
        diff = slot.day_of_week - now.weekday()
        if diff < 0:
            diff += 7
        base_date = now + timedelta(days=diff)
        # Costruisco start e end come datetime
        slot_start = datetime(
            base_date.year,
            base_date.month,
            base_date.day,
            slot.start_time.hour,
            slot.start_time.minute,
            0
        )
        slot_end = datetime(
            base_date.year,
            base_date.month,
            base_date.day,
            slot.end_time.hour,
            slot.end_time.minute,
            0
        )
        # aggiungo a events
        op = User.query.get(slot.operator_id)
        operator_name = op.username if op else "Operatore?"
        events.append({
            "type": "slot",
            "id": slot.id,
            "operator_id": slot.operator_id,
            "operator_name": operator_name,
            "start_time": slot_start.isoformat(),
            "end_time": slot_end.isoformat(),
        })

    # 2) converto appointment in "event"
    #    e aggiungo info su clientName, operatorName
    for app in appointments:
        client = User.query.get(app.client_id)
        operator = User.query.get(app.operator_id)
        events.append({
            "type": "appointment",
            "id": app.id,
            "client_id": app.client_id,
            "operator_id": app.operator_id,
            "clientName": client.username if client else "Cliente?",
            "operatorName": operator.username if operator else "Operatore?",
            "start_time": app.start_time.isoformat(),
            "end_time": app.end_time.isoformat(),
            "service_type": app.service_type,
            "status": app.status,
        })

    # Se user=admin, potremmo ritornare anche la lista pura di "appointments" per le stats
    appointments_list = []
    if user.role == "admin":
        for app in appointments:
            appointments_list.append({
                "id": app.id,
                "client_id": app.client_id,
                "operator_id": app.operator_id,
                "start_time": app.start_time.isoformat(),
                "end_time": app.end_time.isoformat(),
                "service_type": app.service_type,
                "status": app.status,
            })

    resp = {
        "events": events
    }
    if user.role == "admin":
        resp["appointments"] = appointments_list

    return jsonify(resp)

# Prenotazione slot (client/book)
@app.route("/api/client/book", methods=["POST"])
def book_slot():
    data = request.get_json()
    slot_id = data["slot_id"]
    client_id = data["client_id"]

    slot = Slot.query.get_or_404(slot_id)
    client = User.query.get_or_404(client_id)

    # Genera un Appointment (per semplificare, usiamo la "prossima ricorrenza" come sopra)
    now = datetime.now()
    diff = slot.day_of_week - now.weekday()
    if diff < 0:
        diff += 7
    base_date = now + timedelta(days=diff)

    start_time = datetime(
        base_date.year,
        base_date.month,
        base_date.day,
        slot.start_time.hour,
        slot.start_time.minute,
        0
    )
    end_time = datetime(
        base_date.year,
        base_date.month,
        base_date.day,
        slot.end_time.hour,
        slot.end_time.minute,
        0
    )

    # controlla se c'è già un appuntamento in quell'orario
    overlap = Appointment.query.filter(
        Appointment.operator_id == slot.operator_id,
        Appointment.start_time < end_time,
        Appointment.end_time > start_time
    ).first()
    if overlap:
        return jsonify({"error": "Slot già occupato"}), 400

    new_app = Appointment(
        operator_id=slot.operator_id,
        client_id=client_id,
        start_time=start_time,
        end_time=end_time,
        service_type="Prenotazione da cliente",
        status="pending"
    )
    db.session.add(new_app)
    db.session.commit()

    return jsonify({"message": "Appuntamento creato con successo"}), 200

# Esempi di PUT/DELETE per Appuntamenti (admin)
@app.route("/api/admin/appointments/<int:appointment_id>", methods=["PUT", "DELETE"])
def manage_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if request.method == "DELETE":
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({"message": "Appuntamento eliminato"}), 200
    
    # PUT => aggiorna
    data = request.get_json()
    if "start_time" in data:
        appointment.start_time = datetime.fromisoformat(data["start_time"])
    if "end_time" in data:
        appointment.end_time = datetime.fromisoformat(data["end_time"])
    if "service_type" in data:
        appointment.service_type = data["service_type"]
    if "status" in data:
        appointment.status = data["status"]
    db.session.commit()
    return jsonify({"message": "Appuntamento aggiornato"}), 200

# Esempi di PUT/DELETE per Slot (admin)
@app.route("/api/admin/slots/<int:slot_id>", methods=["PUT", "DELETE"])
def manage_slot(slot_id):
    slot = Slot.query.get_or_404(slot_id)
    if request.method == "DELETE":
        db.session.delete(slot)
        db.session.commit()
        return jsonify({"message": "Slot eliminato con successo"}), 200
    
    # PUT => aggiorna
    data = request.get_json()
    if "operator_id" in data:
        slot.operator_id = int(data["operator_id"])
    if "day_of_week" in data:
        slot.day_of_week = int(data["day_of_week"])
    if "start_time" in data:
        hh, mm = data["start_time"].split(":")
        slot.start_time = slot.start_time.replace(hour=int(hh), minute=int(mm))
    if "end_time" in data:
        hh, mm = data["end_time"].split(":")
        slot.end_time = slot.end_time.replace(hour=int(hh), minute=int(mm))
    db.session.commit()
    return jsonify({"message": "Slot aggiornato con successo"}), 200

# API Admin
@app.route('/api/admin/stats/<int:admin_id>', methods=['GET'])
def get_admin_stats(admin_id):
    admin = User.query.filter_by(id=admin_id, role='admin').first()
    if not admin:
        return jsonify({'error': 'Admin non trovato'}), 404

    operators = User.query.filter_by(admin_id=admin_id, role='operator').all()
    op_ids = [op.id for op in operators]
    
    # Calcola statistiche
    total_appointments = Appointment.query.filter(
        Appointment.operator_id.in_(op_ids)
    ).count()
    
    stats = []
    for status in ['pending', 'confirmed', 'completed', 'cancelled']:
        count = Appointment.query.filter(
            Appointment.operator_id.in_(op_ids),
            Appointment.status == status
        ).count()
        stats.append({'name': status.capitalize(), 'value': count})

    return jsonify({
        'totalAppointments': total_appointments,
        'appointmentStats': stats
    })

@app.route('/api/admin/operators/<int:admin_id>', methods=['GET'])
def get_operators(admin_id):
    operators = User.query.filter_by(admin_id=admin_id, role='operator').all()
    return jsonify({
        'operators': [{
            'id': op.id,
            'username': op.username,
            'email': op.email,
            'phone': op.phone,
            'specialization': op.specialization
        } for op in operators]
    })
@app.route('/api/slots', methods=['GET'])
def get_slots():
    slots = Slot.query.filter_by(is_active=True).all()
    return jsonify({
        'slots': [{
            'id': slot.id,
            'operator_id': slot.operator_id,
            'operator_name': User.query.get(slot.operator_id).username,
            'day_of_week': slot.day_of_week,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M')
        } for slot in slots]
    })

@app.route('/api/admin/appointments/<int:appointment_id>', methods=['PUT', 'DELETE'])
def manage_appointment_by_id(appointment_id):
    from datetime import datetime
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if request.method == 'DELETE':
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({'message': 'Appuntamento eliminato con successo'}), 200
    
    # Se PUT, aggiorna i campi
    data = request.get_json()
    if 'start_time' in data:
        # parse da ISO string
        appointment.start_time = datetime.fromisoformat(data['start_time'])
    if 'end_time' in data:
        appointment.end_time = datetime.fromisoformat(data['end_time'])
    if 'service_type' in data:
        appointment.service_type = data['service_type']
    if 'status' in data:
        appointment.status = data['status']
    db.session.commit()
    
    return jsonify({'message': 'Appuntamento aggiornato con successo'}), 200


@app.route('/api/admin/slots/<int:slot_id>', methods=['PUT', 'DELETE'])
def manage_slot_by_id(slot_id):
    slot = Slot.query.get_or_404(slot_id)
    
    if request.method == 'DELETE':
        db.session.delete(slot)
        db.session.commit()
        return jsonify({'message': 'Slot eliminato con successo'}), 200
    
    # Se PUT, aggiorna i campi
    data = request.get_json()
    if 'operator_id' in data:
        slot.operator_id = data['operator_id']
    if 'day_of_week' in data:
        slot.day_of_week = int(data['day_of_week'])
    if 'start_time' in data:
        # Esempio: se arriva "10:00", parse come time
        from datetime import time
        hh, mm = data['start_time'].split(':')
        slot.start_time = time(int(hh), int(mm))
    if 'end_time' in data:
        from datetime import time
        hh, mm = data['end_time'].split(':')
        slot.end_time = time(int(hh), int(mm))
    
    db.session.commit()
    return jsonify({'message': 'Slot aggiornato con successo'}), 200


@app.route('/api/admin/operators/add', methods=['POST'])
def add_operator():
    data = request.get_json()
    admin_id = data['admin_id']
    
    # Verifica admin
    admin = User.query.filter_by(id=admin_id, role='admin').first()
    if not admin:
        return jsonify({'error': 'Non autorizzato'}), 403

    # Verifica duplicati
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username esistente'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email esistente'}), 400

    # Crea operatore
    hashed_password = generate_password_hash(data['password'], method='scrypt')
    new_operator = User(
        username=data['username'],
        password_hash=hashed_password,
        email=data['email'],
        phone=data.get('phone', ''),
        role='operator',
        admin_id=admin_id,
        specialization=data.get('specialization', '')
    )
    
    db.session.add(new_operator)
    db.session.commit()
    
    return jsonify({'message': 'Operatore creato con successo'})

@app.route('/api/admin/send-reminders', methods=['POST'])
def send_reminders():
    try:
        # Trova gli appuntamenti di domani
        tomorrow = datetime.now() + timedelta(days=1)
        appointments = Appointment.query.filter(
            Appointment.start_time >= tomorrow.replace(hour=0, minute=0, second=0),
            Appointment.start_time < tomorrow.replace(hour=23, minute=59, second=59)
        ).all()

        # Invia notifiche WhatsApp
        for app in appointments:
            client = User.query.get(app.client_id)
            if client.phone:
                message = f"Gentile {client.username}, ti ricordiamo il tuo appuntamento domani alle {app.start_time.strftime('%H:%M')}."
                send_whatsapp_notification(client.phone, message)

        return jsonify({'message': 'Notifiche inviate con successo'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Servizi
@app.route('/api/admin/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify({
        'services': [{
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'duration': s.duration,
            'price': float(s.price)
        } for s in services]
    })

@app.route('/api/admin/services/add', methods=['POST'])
def add_service():
    data = request.get_json()
    new_service = Service(
        name=data['name'],
        description=data['description'],
        duration=int(data['duration']),
        price=float(data['price'])
    )
    db.session.add(new_service)
    db.session.commit()
    return jsonify({'message': 'Servizio creato con successo'})

@app.route('/api/admin/services/<int:service_id>', methods=['PUT', 'DELETE'])
def manage_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    if request.method == 'DELETE':
        db.session.delete(service)
        db.session.commit()
        return jsonify({'message': 'Servizio eliminato'})
    
    # PUT
    data = request.get_json()
    service.name = data.get('name', service.name)
    service.description = data.get('description', service.description)
    service.duration = int(data.get('duration', service.duration))
    service.price = float(data.get('price', service.price))
    db.session.commit()
    return jsonify({'message': 'Servizio aggiornato'})

# API Appointments
@app.route('/api/admin/appointments/<int:admin_id>', methods=['GET'])
def get_appointments(admin_id):
    operators = User.query.filter_by(admin_id=admin_id, role='operator').all()
    op_ids = [op.id for op in operators]
    
    appointments = Appointment.query.filter(
        Appointment.operator_id.in_(op_ids)
    ).all()
    
    return jsonify({
        'appointments': [{
            'id': app.id,
            'start_time': app.start_time.isoformat(),
            'end_time': app.end_time.isoformat(),
            'operatorId': app.operator_id,
            'operatorName': User.query.get(app.operator_id).username,
            'clientName': User.query.get(app.client_id).username,
            'status': app.status,
            'service_type': app.service_type
        } for app in appointments]
    })

    

@app.route('/api/admin/appointments', methods=['POST'])
def add_appointment():
    data = request.get_json()
    
    operator = User.query.get(data['operator_id'])
    client = User.query.get(data['client_id'])
    
    if not operator or not client:
        return jsonify({'error': 'Operatore o cliente non valido'}), 400

    new_appointment = Appointment(
        operator_id=operator.id,
        client_id=client.id,
        start_time=datetime.fromisoformat(data['start_time']),
        end_time=datetime.fromisoformat(data['end_time']),
        service_type=data['service_type']
    )
    
    db.session.add(new_appointment)
    db.session.commit()
    
    # Notifica WhatsApp al cliente
    if client.phone:
        send_whatsapp_notification(
            client.phone,
            f"Nuovo appuntamento creato per il {new_appointment.start_time.strftime('%d/%m/%Y %H:%M')}"
        )
    
    return jsonify({'message': 'Appuntamento creato con successo'})

# API Slots
@app.route('/api/admin/slots/add', methods=['POST'])
def add_slot():
    data = request.get_json()
    
    # Verifica operatore
    operator = User.query.filter_by(id=data['operator_id'], role='operator').first()
    if not operator:
        return jsonify({'error': 'Operatore non valido'}), 400

    # Crea nuovo slot
    new_slot = Slot(
        operator_id=operator.id,
        day_of_week=data['day_of_week'],  # 0-6 per Lun-Dom
        start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
        end_time=datetime.strptime(data['end_time'], '%H:%M').time(),
        is_active=True
    )
    
    db.session.add(new_slot)
    db.session.commit()
    
    return jsonify({
        'message': 'Slot creato con successo',
        'slot': {
            'id': new_slot.id,
            'operatorId': new_slot.operator_id,
            'day_of_week': new_slot.day_of_week,
            'start_time': new_slot.start_time.strftime('%H:%M'),
            'end_time': new_slot.end_time.strftime('%H:%M')
        }
    })

    
# API Client
@app.route('/api/client/book', methods=['POST'])
def book_slot():
    data = request.get_json()
    
    slot = Slot.query.get_or_404(data['slot_id'])
    client = User.query.get_or_404(data['client_id'])
    
    if not slot.is_active:
        return jsonify({'error': 'Slot non disponibile'}), 400

    # Calcola la data del prossimo slot disponibile
    now = datetime.now()
    days_ahead = (slot.day_of_week - now.weekday()) % 7
    slot_date = now.date() + timedelta(days=days_ahead)
    
    start_time = datetime.combine(slot_date, slot.start_time)
    end_time = datetime.combine(slot_date, slot.end_time)
    
    # Verifica sovrapposizioni
    existing = Appointment.query.filter(
        Appointment.operator_id == slot.operator_id,
        Appointment.start_time < end_time,
        Appointment.end_time > start_time
    ).first()
    
    if existing:
        return jsonify({'error': 'Slot già occupato'}), 400
        
    # Crea l'appuntamento
    new_appointment = Appointment(
        operator_id=slot.operator_id,
        client_id=client.id,
        start_time=start_time,
        end_time=end_time,
        status='pending',
        service_type='Prenotazione da cliente'
    )
    
    db.session.add(new_appointment)
    db.session.commit()

    # Invia notifica WhatsApp se disponibile
    operator = User.query.get(slot.operator_id)
    if operator.phone:
        send_whatsapp_notification(
            operator.phone,
            f"Nuova prenotazione da {client.username} per {start_time.strftime('%d/%m/%Y %H:%M')}"
        )
    
    return jsonify({'message': 'Prenotazione effettuata con successo'})

@app.route('/api/admin/clients/<int:admin_id>', methods=['GET'])
def get_clients(admin_id):
    # Verifica che sia un admin
    admin = User.query.filter_by(id=admin_id, role='admin').first()
    if not admin:
        return jsonify({'error': 'Non autorizzato'}), 403
        
    # Ottieni tutti i clienti dell'admin
    clients = User.query.filter_by(admin_id=admin_id, role='client').all()
    
    return jsonify({
        'clients': [{
            'id': c.id,
            'username': c.username,
            'password_hash': c.password_hash,
            'email': c.email,
            'phone': c.phone
        } for c in clients]
    })

@app.route('/api/admin/notify/whatsapp', methods=['POST'])
def send_admin_whatsapp():
    data = request.get_json()
    admin_id = data.get('admin_id')
    message = data.get('message', 'Notifica dal tuo Admin')
    
    # Verifica admin
    admin = User.query.filter_by(id=admin_id, role='admin').first()
    if not admin:
        return jsonify({'error': 'Admin non trovato'}), 404
        
    # Invia a tutti i clienti dell'admin
    clients = User.query.filter_by(admin_id=admin_id, role='client').all()
    sent_count = 0
    
    for client in clients:
        if client.phone:
            if send_whatsapp_notification(client.phone, message):
                sent_count += 1
                
    return jsonify({
        'message': f'Notifiche inviate a {sent_count} clienti',
        'success': True
    })

if __name__ == '__main__':
    print(">>> Avvio server Flask su http://localhost:5000")
    print(">>> Reindirizzamento a Frontend React su http://localhost:3000")
    app.run(debug=True, port=5000)