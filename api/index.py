##############################################################################
# app.py - Esempio completo di backend Flask collegato a MySQL
##############################################################################
from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

##############################################################################
# CONFIGURAZIONE FLASK E DB
##############################################################################
app = Flask(__name__)

# Credenziali del DB
db_user = "root"
db_password = "lollo201416"
db_host = "34.17.85.107"
db_name = "appointment_db"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "chiave_super_segreta_123"

db = SQLAlchemy(app)
# Configura i CORS
CORS(
    app,
    resources={r"/*": {"origins": [
        "http://localhost:3000",  # Per il testing in locale
        "https://clientappo-r3ghpgiu1-andreasettannis-projects.vercel.app",  # Nuovo frontend su Vercel
        "https://appo-liard.vercel.app",  # Vecchio frontend (se esiste ancora)
        "https://appo-wjc5-h09acpeed-andreasettannis-projects.vercel.app",  # URL backend diretto
        "https://mioalias.vercel.app",  # Alias backend
    ]}},
    supports_credentials=True,
)



##############################################################################
# MODELLI (tabelle DB)
##############################################################################
class User(db.Model):
    """
    Modello che rappresenta l'utente:
    - role può essere: admin, operator, client
    - admin_id: se un client o operator è creato da un certo admin
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default="client")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    specialization = db.Column(db.String(100), nullable=True)


class Appointment(db.Model):
    """
    Modello che rappresenta un appuntamento
    tra un client e un operatore.
    """
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    service_type = db.Column(db.String(100))
    status = db.Column(db.String(20), default="pending")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Slot(db.Model):
    """
    Modello per la richiesta di uno slot di disponibilità
    (da parte del client), può essere pending, approved, rejected
    """
    __tablename__ = "slots"

    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0 (Domenica) - 6 (Sabato)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default="pending")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

##############################################################################
# UTILITY (es. invio notifiche WhatsApp)
##############################################################################
def send_whatsapp_notification(to_number, message):
    """
    Invia messaggi su WhatsApp (finto, senza Twilio).
    """
    print(f"[FAKE] Invio WhatsApp a {to_number}: {message}")
    return True

##############################################################################
# ROUTE DI BASE
##############################################################################
@app.route("/")
def index_root():
    """
    Route principale (root). Utile per verificare se il server è attivo.
    """
    return "Server Flask attivo!"


@app.route("/api")
def index_api():
    """
    Endpoint /api per un test rapido:
    Se fai 'curl https://.../api', ricevi questo messaggio.
    """
    return jsonify({"message": "Benvenuto nell'API!"})

##############################################################################
# AUTH
##############################################################################
@app.route("/api/auth/register", methods=["POST"])
def register():
    """
    Registra un nuovo utente (admin, operator, client).

    Esempio JSON:
    {
      "username": "...",
      "password": "...",
      "email": "...",
      "phone": "...",
      "role": "admin" (opzionale, default client)
      "admin_id": 1 (se un admin registra un client, opzionale)
    }
    """
    data = request.get_json()
    # Controlla se username esiste
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username già esistente"}), 400
    # Controlla se email esiste
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email già esistente"}), 400

    hashed = generate_password_hash(data["password"], method="scrypt")
    new_user = User(
        username=data["username"],
        password_hash=hashed,
        email=data["email"],
        phone=data.get("phone", ""),
        role=data.get("role", "client"),
        admin_id=data.get("admin_id"),
    )
    db.session.add(new_user)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Registrazione completata",
                "user": {
                    "id": new_user.id,
                    "username": new_user.username,
                    "email": new_user.email,
                    "role": new_user.role,
                },
            }
        ),
        201,
    )


@app.route("/api/auth/login", methods=["POST"])
def login():
    """
    Login di un utente esistente

    Esempio JSON:
    {
      "username": "...",
      "password": "..."
    }
    """
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    if user and check_password_hash(user.password_hash, data["password"]):
        return (
            jsonify(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "admin_id": user.admin_id,
                        "phone": user.phone,
                    }
                }
            ),
            200,
        )
    return jsonify({"error": "Credenziali non valide"}), 401

##############################################################################
# CALENDARIO (slot e appuntamenti)
##############################################################################
@app.route("/api/calendar/<int:user_id>", methods=["GET"])
def get_calendar_data(user_id):
    """
    Restituisce tutti gli slot + appuntamenti visibili per quell'utente.
    Admin: vede tutto.
    Operator: vede i propri.
    Client: vede i propri app + slot 'approved'.
    """
    user = User.query.get_or_404(user_id)
    events = []

    if user.role == "admin":
        slots = Slot.query.all()
        appointments = Appointment.query.all()
    elif user.role == "operator":
        slots = Slot.query.filter_by(operator_id=user.id).all()
        appointments = Appointment.query.filter_by(operator_id=user.id).all()
    else:
        # client
        slots = Slot.query.filter_by(status="approved").all()
        appointments = Appointment.query.filter_by(client_id=user.id).all()

    # Convertiamo gli slot in eventi
    now = datetime.now()
    for s in slots:
        diff = s.day_of_week - now.weekday()
        if diff < 0:
            diff += 7
        base_date = now.date() + timedelta(days=diff)
        start_dt = datetime.combine(base_date, s.start_time)
        end_dt = datetime.combine(base_date, s.end_time)

        operator_obj = User.query.get(s.operator_id)
        operator_name = operator_obj.username if operator_obj else "???"

        events.append(
            {
                "type": "slot",
                "id": f"slot-{s.id}",
                "slot_id": s.id,
                "operator_id": s.operator_id,
                "operator_name": operator_name,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "status": s.status,
            }
        )

    # Convertiamo gli appuntamenti in eventi
    for appo in appointments:
        client_obj = User.query.get(appo.client_id)
        operator_obj = User.query.get(appo.operator_id)
        events.append(
            {
                "type": "appointment",
                "id": appo.id,
                "client_id": appo.client_id,
                "operator_id": appo.operator_id,
                "clientName": client_obj.username if client_obj else "???",
                "operatorName": operator_obj.username if operator_obj else "???",
                "start_time": appo.start_time.isoformat(),
                "end_time": appo.end_time.isoformat(),
                "service_type": appo.service_type,
                "status": appo.status,
            }
        )

    return jsonify({"events": events}), 200

##############################################################################
# ADMIN - OPERATORS, CLIENTS, APPOINTMENTS
##############################################################################
@app.route("/api/admin/operators/<int:admin_id>", methods=["GET"])
def get_operators(admin_id):
    """
    Restituisce tutti gli operatori creati da un certo admin_id.
    """
    ops = User.query.filter_by(admin_id=admin_id, role="operator").all()
    return jsonify(
        {
            "operators": [
                {
                    "id": o.id,
                    "username": o.username,
                    "email": o.email,
                    "phone": o.phone,
                    "specialization": o.specialization,
                }
                for o in ops
            ]
        }
    ), 200


@app.route("/api/admin/clients/<int:admin_id>", methods=["GET"])
def get_clients(admin_id):
    """
    Restituisce tutti i client di un admin specifico.
    """
    admin = User.query.filter_by(id=admin_id, role="admin").first()
    if not admin:
        return jsonify({"error": "Non autorizzato"}), 403

    clients = User.query.filter_by(admin_id=admin_id, role="client").all()
    return (
        jsonify(
            {
                "clients": [
                    {
                        "id": c.id,
                        "username": c.username,
                        "email": c.email,
                        "phone": c.phone,
                    }
                    for c in clients
                ]
            }
        ),
        200,
    )


@app.route("/api/admin/operators/add", methods=["POST"])
def add_operator():
    """
    Aggiunge un nuovo operatore (creato da un admin).

    Esempio JSON:
    {
      "admin_id": 1,
      "username": "...",
      "password": "...",
      "email": "...",
      "phone": "...",
      "specialization": "..."
    }
    """
    data = request.get_json()
    admin = User.query.filter_by(id=data["admin_id"], role="admin").first()
    if not admin:
        return jsonify({"error": "Non autorizzato"}), 403

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username esistente"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email esistente"}), 400

    hashed = generate_password_hash(data["password"], method="scrypt")
    new_op = User(
        username=data["username"],
        password_hash=hashed,
        email=data["email"],
        phone=data.get("phone", ""),
        role="operator",
        admin_id=data["admin_id"],
        specialization=data.get("specialization", ""),
    )
    db.session.add(new_op)
    db.session.commit()
    return jsonify({"message": "Operatore creato con successo"}), 200


@app.route("/api/admin/appointments", methods=["POST"])
def add_appointment():
    """
    Crea un nuovo appuntamento

    Esempio JSON:
    {
      "operator_id": 2,
      "client_id": 10,
      "start_time": "2025-01-31T10:00:00",
      "end_time": "2025-01-31T10:30:00",
      "service_type": "taglio capelli"
    }
    """
    data = request.get_json()
    operator = User.query.get(data["operator_id"])
    client = User.query.get(data["client_id"])
    if not operator or not client:
        return jsonify({"error": "Operatore o cliente non valido"}), 400

    new_app = Appointment(
        operator_id=operator.id,
        client_id=client.id,
        start_time=datetime.fromisoformat(data["start_time"]),
        end_time=datetime.fromisoformat(data["end_time"]),
        service_type=data.get("service_type", ""),
    )
    db.session.add(new_app)
    db.session.commit()

    # Notifica finta su WhatsApp
    if client.phone:
        send_whatsapp_notification(
            client.phone,
            f"Nuovo appuntamento creato per il {new_app.start_time.strftime('%d/%m/%Y %H:%M')}",
        )
    return jsonify({"message": "Appuntamento creato con successo"}), 200


@app.route("/api/admin/appointments/<int:appointment_id>", methods=["PUT", "DELETE"])
def manage_appointment_by_id(appointment_id):
    """
    Aggiorna o elimina un appuntamento.

    PUT Esempio JSON:
    {
      "start_time": "2025-01-31T11:00:00",
      "end_time": "2025-01-31T11:30:00",
      "service_type": "taglio capelli",
      "status": "approved"
    }
    """
    appo = Appointment.query.get_or_404(appointment_id)
    if request.method == "DELETE":
        db.session.delete(appo)
        db.session.commit()
        return jsonify({"message": "Appuntamento eliminato"}), 200

    data = request.get_json()
    if "start_time" in data:
        appo.start_time = datetime.fromisoformat(data["start_time"])
    if "end_time" in data:
        appo.end_time = datetime.fromisoformat(data["end_time"])
    if "service_type" in data:
        appo.service_type = data["service_type"]
    if "status" in data:
        appo.status = data["status"]

    db.session.commit()
    return jsonify({"message": "Appuntamento aggiornato"}), 200

##############################################################################
# Notifiche WhatsApp
##############################################################################
@app.route("/api/admin/send-reminders", methods=["POST"])
def send_reminders():
    """
    Esempio di invio reminder per gli appuntamenti di domani.
    """
    try:
        tomorrow = datetime.now() + timedelta(days=1)
        start_tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end_tomorrow = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

        appointments = Appointment.query.filter(
            Appointment.start_time >= start_tomorrow,
            Appointment.start_time <= end_tomorrow
        ).all()

        for a in appointments:
            client = User.query.get(a.client_id)
            if client and client.phone:
                msg = (
                    f"Reminder: hai un appuntamento domani alle "
                    f"{a.start_time.strftime('%H:%M')}"
                )
                send_whatsapp_notification(client.phone, msg)

        return jsonify({"message": "Notifiche inviate"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

##############################################################################
# GESTIONE SLOT PENDING (ADMIN)
##############################################################################
@app.route("/api/admin/slots/pending", methods=["GET"])
def get_pending_slots():
    """
    Restituisce tutti gli slot con status='pending'.
    """
    slots = Slot.query.filter_by(status="pending").all()
    return (
        jsonify(
            {
                "slots": [
                    {
                        "id": s.id,
                        "operator_id": s.operator_id,
                        "client_id": s.client_id,
                        "day_of_week": s.day_of_week,
                        "start_time": s.start_time.strftime("%H:%M"),
                        "end_time": s.end_time.strftime("%H:%M"),
                        "status": s.status,
                    }
                    for s in slots
                ]
            }
        ),
        200,
    )


@app.route("/api/admin/slots/<int:slot_id>/approve", methods=["PUT"])
def approve_slot(slot_id):
    """
    Approva uno slot in stato 'pending'.
    """
    slot = Slot.query.get_or_404(slot_id)
    slot.status = "approved"
    db.session.commit()
    return jsonify({"message": "Slot approvato con successo"}), 200


@app.route("/api/admin/slots/<int:slot_id>/reject", methods=["PUT"])
def reject_slot(slot_id):
    """
    Rifiuta uno slot in stato 'pending'.
    """
    slot = Slot.query.get_or_404(slot_id)
    slot.status = "rejected"
    db.session.commit()
    return jsonify({"message": "Slot rifiutato"}), 200

##############################################################################
# CLIENT: RICHIESTA SLOT
##############################################################################
@app.route("/api/client/slots/request", methods=["POST"])
def request_slot():
    """
    Un client può richiedere uno slot (status="pending").

    Esempio JSON:
    {
      "client_id": 10,
      "operator_id": 2,
      "day_of_week": 3,
      "start_time": "09:00",
      "end_time": "10:00"
    }
    """
    data = request.get_json()
    client_id = data["client_id"]
    operator_id = data["operator_id"]

    client = User.query.get(client_id)
    operator = User.query.get(operator_id)
    if not client or not operator:
        return jsonify({"error": "Client o operator non valido"}), 400

    day_of_week = int(data["day_of_week"])
    start_t = datetime.strptime(data["start_time"], "%H:%M").time()
    end_t = datetime.strptime(data["end_time"], "%H:%M").time()

    new_slot = Slot(
        operator_id=operator.id,
        client_id=client.id,
        day_of_week=day_of_week,
        start_time=start_t,
        end_time=end_t,
        status="pending",
        is_active=True,
    )
    db.session.add(new_slot)
    db.session.commit()
    return jsonify({"message": "Richiesta slot inviata"}), 201

##############################################################################
# MAIN
##############################################################################
if __name__ == "__main__":
    # Crea le tabelle nel DB (se non esistono)
    with app.app_context():
        db.create_all()

    print(">>> Avvio server Flask su http://localhost:5000")
    app.run(debug=True, port=5000)

