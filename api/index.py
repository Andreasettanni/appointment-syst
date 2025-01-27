from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import text
import time

##############################################################################
# CONFIGURAZIONE FLASK E DB
##############################################################################
app = Flask(__name__)

# Credenziali del DB
db_user = "root"
db_password = "lollo201416"
db_host = "34.17.85.107"
db_name = "appointment_db"

# Configurazione ottimizzata del database per Vercel
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    "?connect_timeout=5"  # Timeout ridotto per Vercel
)

# Configurazione ottimizzata del pool di connessioni
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 5,  # Ridotto per Vercel
    "max_overflow": 10,
    "pool_timeout": 5,
    "pool_recycle": 1800,
    "pool_pre_ping": True,
    "connect_args": {
        "connect_timeout": 5,
        "read_timeout": 5,
        "write_timeout": 5
    }
}

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "chiave_super_segreta_123"

db = SQLAlchemy(app)

# Configura i CORS
CORS(
    app,
    resources={r"/*": {"origins": [
        "http://localhost:3000",
        "https://clientappo.vercel.app",  # Frontend principale
        "https://appointment-syst.vercel.app",  # Backend URL
        "https://clientappo-nadesud1b-andreasettannis-projects.vercel.app",
        "https://clientappo-r3ghpgiu1-andreasettannis-projects.vercel.app",
        "https://appo-liard.vercel.app",
        "https://appo-wjc5-h09acpeed-andreasettannis-projects.vercel.app",
        "https://mioalias.vercel.app"
    ]}},
    supports_credentials=True,
    expose_headers=["Access-Control-Allow-Origin"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600
)

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    allowed_origins = [
        "http://localhost:3000",
        "https://clientappo.vercel.app",
        "https://appointment-syst.vercel.app",
        "https://clientappo-nadesud1b-andreasettannis-projects.vercel.app",
        "https://clientappo-r3ghpgiu1-andreasettannis-projects.vercel.app",
        "https://appo-liard.vercel.app",
        "https://appo-wjc5-h09acpeed-andreasettannis-projects.vercel.app",
        "https://mioalias.vercel.app"
    ]
    
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

# Continua dal codice precedente...

# Tutte le route OPTIONS in un'unica funzione
@app.route("/api/auth/register", methods=["OPTIONS"])
@app.route("/api/auth/login", methods=["OPTIONS"])
@app.route("/api/calendar/<int:user_id>", methods=["OPTIONS"])
@app.route("/api/admin/operators/<int:admin_id>", methods=["OPTIONS"])
@app.route("/api/admin/clients/<int:admin_id>", methods=["OPTIONS"])
@app.route("/api/admin/operators/add", methods=["OPTIONS"])
@app.route("/api/admin/appointments", methods=["OPTIONS"])
@app.route("/api/admin/appointments/<int:appointment_id>", methods=["OPTIONS"])
@app.route("/api/admin/slots/pending", methods=["OPTIONS"])
@app.route("/api/admin/slots/<int:slot_id>/approve", methods=["OPTIONS"])
@app.route("/api/admin/slots/<int:slot_id>/reject", methods=["OPTIONS"])
@app.route("/api/client/slots/request", methods=["OPTIONS"])
def handle_preflight():
    response = jsonify({"message": "OK"})
    return response

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
    Modello per gli slot di disponibilità
    """
    __tablename__ = "slots"

    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default="pending")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

##############################################################################
# UTILITY
##############################################################################
def send_whatsapp_notification(to_number, message):
    """
    Invia messaggi su WhatsApp (simulato)
    """
    print(f"[FAKE] Invio WhatsApp a {to_number}: {message}")
    return True

##############################################################################
# ROUTE DI BASE
##############################################################################
@app.route("/")
def index_root():
    return "Server Flask attivo!"

@app.route("/api")
def index_api():
    return jsonify({"message": "Benvenuto nell'API!"})

@app.route("/api/auth/register", methods=["POST"])
def register():
    """
    Registrazione ottimizzata per Vercel
    """
    try:
        start_time = time.time()
        app.logger.info("Inizio registrazione")
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dati mancanti"}), 400

        # Validazione veloce
        required = ["username", "password", "email"]
        if not all(field in data for field in required):
            return jsonify({"error": "Campi obbligatori mancanti"}), 400

        # Check duplicati ottimizzato
        with db.engine.connect().execution_options(timeout=5) as conn:
            result = conn.execute(
                text("""
                    SELECT username, email FROM users 
                    WHERE username = :username OR email = :email 
                    LIMIT 1
                """),
                {"username": data["username"], "email": data["email"]}
            ).fetchone()
            
            if result:
                if result.username == data["username"]:
                    return jsonify({"error": "Username già esistente"}), 400
                return jsonify({"error": "Email già esistente"}), 400

        # Creazione utente ottimizzata
        hashed = generate_password_hash(data["password"], method="scrypt")
        with db.engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO users (username, password_hash, email, phone, role, admin_id, created_at) 
                    VALUES (:username, :password, :email, :phone, :role, :admin_id, NOW())
                """),
                {
                    "username": data["username"],
                    "password": hashed,
                    "email": data["email"],
                    "phone": data.get("phone", ""),
                    "role": data.get("role", "client"),
                    "admin_id": data.get("admin_id")
                }
            )
            conn.commit()
            new_user_id = result.lastrowid

        execution_time = time.time() - start_time
        app.logger.info(f"Registrazione completata in {execution_time:.2f} secondi")

        return jsonify({
            "message": "Registrazione completata",
            "user": {
                "id": new_user_id,
                "username": data["username"],
                "email": data["email"],
                "role": data.get("role", "client")
            }
        }), 201

    except Exception as e:
        app.logger.error(f"Errore registrazione: {str(e)}")
        return jsonify({"error": "Errore durante la registrazione"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    """
    Login ottimizzato per Vercel
    """
    try:
        start_time = time.time()
        app.logger.info("Inizio login")
        
        data = request.get_json()
        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "Credenziali mancanti"}), 400

        # Query ottimizzata
        with db.engine.connect().execution_options(timeout=5) as conn:
            result = conn.execute(
                text("""
                    SELECT id, username, password_hash, email, role, admin_id, phone 
                    FROM users 
                    WHERE username = :username 
                    LIMIT 1
                """),
                {"username": data["username"]}
            ).fetchone()

            if not result or not check_password_hash(result.password_hash, data["password"]):
                return jsonify({"error": "Credenziali non valide"}), 401

            execution_time = time.time() - start_time
            app.logger.info(f"Login completato in {execution_time:.2f} secondi")

            return jsonify({
                "user": {
                    "id": result.id,
                    "username": result.username,
                    "email": result.email,
                    "role": result.role,
                    "admin_id": result.admin_id,
                    "phone": result.phone
                }
            }), 200

    except Exception as e:
        app.logger.error(f"Errore login: {str(e)}")
        return jsonify({"error": "Errore durante il login"}), 500

@app.route("/api/calendar/<int:user_id>", methods=["GET"])
def get_calendar_data(user_id):
    """
    Calendar data ottimizzato per Vercel
    """
    try:
        start_time = time.time()
        app.logger.info(f"Richiesta calendario per user_id: {user_id}")

        # Query ottimizzata per utente
        with db.engine.connect().execution_options(timeout=5) as conn:
            user = conn.execute(
                text("SELECT role FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()

            if not user:
                return jsonify({"error": "Utente non trovato"}), 404

            # Query ottimizzate per slot e appuntamenti
            if user.role == "admin":
                slots = conn.execute(text("SELECT * FROM slots")).fetchall()
                appointments = conn.execute(text("SELECT * FROM appointments")).fetchall()
            elif user.role == "operator":
                slots = conn.execute(
                    text("SELECT * FROM slots WHERE operator_id = :user_id"),
                    {"user_id": user_id}
                ).fetchall()
                appointments = conn.execute(
                    text("SELECT * FROM appointments WHERE operator_id = :user_id"),
                    {"user_id": user_id}
                ).fetchall()
            else:  # client
                slots = conn.execute(
                    text("SELECT * FROM slots WHERE status = 'approved'")
                ).fetchall()
                appointments = conn.execute(
                    text("SELECT * FROM appointments WHERE client_id = :user_id"),
                    {"user_id": user_id}
                ).fetchall()

            events = []
            now = datetime.now()

            # Processo gli slot
            for s in slots:
                diff = s.day_of_week - now.weekday()
                if diff < 0:
                    diff += 7
                base_date = now.date() + timedelta(days=diff)
                start_dt = datetime.combine(base_date, s.start_time)
                end_dt = datetime.combine(base_date, s.end_time)

                # Get operator info
                operator = conn.execute(
                    text("SELECT username FROM users WHERE id = :op_id"),
                    {"op_id": s.operator_id}
                ).fetchone()

                events.append({
                    "type": "slot",
                    "id": f"slot-{s.id}",
                    "slot_id": s.id,
                    "operator_id": s.operator_id,
                    "operator_name": operator.username if operator else "???",
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                    "status": s.status,
                })

            # Processo gli appuntamenti
            for appo in appointments:
                client = conn.execute(
                    text("SELECT username FROM users WHERE id = :client_id"),
                    {"client_id": appo.client_id}
                ).fetchone()
                operator = conn.execute(
                    text("SELECT username FROM users WHERE id = :op_id"),
                    {"op_id": appo.operator_id}
                ).fetchone()

                events.append({
                    "type": "appointment",
                    "id": appo.id,
                    "client_id": appo.client_id,
                    "operator_id": appo.operator_id,
                    "clientName": client.username if client else "???",
                    "operatorName": operator.username if operator else "???",
                    "start_time": appo.start_time.isoformat(),
                    "end_time": appo.end_time.isoformat(),
                    "service_type": appo.service_type,
                    "status": appo.status,
                })

            execution_time = time.time() - start_time
            app.logger.info(f"Calendario generato in {execution_time:.2f} secondi")

            return jsonify({"events": events}), 200

    except Exception as e:
        app.logger.error(f"Errore calendario: {str(e)}")
        return jsonify({"error": "Errore durante il recupero del calendario"}), 500

@app.route("/api/admin/operators/<int:admin_id>", methods=["GET"])
def get_operators(admin_id):
    """
    Lista operatori ottimizzata
    """
    try:
        with db.engine.connect().execution_options(timeout=5) as conn:
            operators = conn.execute(
                text("""
                    SELECT id, username, email, phone, specialization 
                    FROM users 
                    WHERE admin_id = :admin_id AND role = 'operator'
                """),
                {"admin_id": admin_id}
            ).fetchall()

            return jsonify({
                "operators": [{
                    "id": op.id,
                    "username": op.username,
                    "email": op.email,
                    "phone": op.phone,
                    "specialization": op.specialization
                } for op in operators]
            }), 200

    except Exception as e:
        app.logger.error(f"Errore recupero operatori: {str(e)}")
        return jsonify({"error": "Errore durante il recupero degli operatori"}), 500

@app.route("/api/admin/clients/<int:admin_id>", methods=["GET"])
def get_clients(admin_id):
    """
    Lista clienti ottimizzata
    """
    try:
        with db.engine.connect().execution_options(timeout=5) as conn:
            # Verifica admin
            admin = conn.execute(
                text("SELECT id FROM users WHERE id = :id AND role = 'admin'"),
                {"id": admin_id}
            ).fetchone()
            
            if not admin:
                return jsonify({"error": "Non autorizzato"}), 403

            clients = conn.execute(
                text("""
                    SELECT id, username, email, phone 
                    FROM users 
                    WHERE admin_id = :admin_id AND role = 'client'
                """),
                {"admin_id": admin_id}
            ).fetchall()

            return jsonify({
                "clients": [{
                    "id": c.id,
                    "username": c.username,
                    "email": c.email,
                    "phone": c.phone
                } for c in clients]
            }), 200

    except Exception as e:
        app.logger.error(f"Errore recupero clienti: {str(e)}")
        return jsonify({"error": "Errore durante il recupero dei clienti"}), 500

@app.route("/api/admin/operators/add", methods=["POST"])
def add_operator():
    """
    Aggiunta operatore ottimizzata
    """
    try:
        start_time = time.time()
        data = request.get_json()

        with db.engine.connect().execution_options(timeout=5) as conn:
            # Verifica admin
            admin = conn.execute(
                text("SELECT id FROM users WHERE id = :id AND role = 'admin'"),
                {"id": data["admin_id"]}
            ).fetchone()
            
            if not admin:
                return jsonify({"error": "Non autorizzato"}), 403

            # Verifica duplicati
            existing = conn.execute(
                text("""
                    SELECT username, email FROM users 
                    WHERE username = :username OR email = :email
                """),
                {"username": data["username"], "email": data["email"]}
            ).fetchone()

            if existing:
                if existing.username == data["username"]:
                    return jsonify({"error": "Username esistente"}), 400
                return jsonify({"error": "Email esistente"}), 400

            # Creazione operatore
            hashed = generate_password_hash(data["password"], method="scrypt")
            result = conn.execute(
                text("""
                    INSERT INTO users (username, password_hash, email, phone, role, 
                                    admin_id, specialization, created_at) 
                    VALUES (:username, :password, :email, :phone, 'operator', 
                            :admin_id, :specialization, NOW())
                """),
                {
                    "username": data["username"],
                    "password": hashed,
                    "email": data["email"],
                    "phone": data.get("phone", ""),
                    "admin_id": data["admin_id"],
                    "specialization": data.get("specialization", "")
                }
            )
            conn.commit()

            execution_time = time.time() - start_time
            app.logger.info(f"Operatore creato in {execution_time:.2f} secondi")

            return jsonify({"message": "Operatore creato con successo"}), 200

    except Exception as e:
        app.logger.error(f"Errore creazione operatore: {str(e)}")
        return jsonify({"error": "Errore durante la creazione dell'operatore"}), 500

@app.route("/api/admin/appointments", methods=["POST"])
def add_appointment():
    """
    Creazione appuntamento ottimizzata
    """
    try:
        start_time = time.time()
        data = request.get_json()

        with db.engine.connect().execution_options(timeout=5) as conn:
            # Verifica esistenza utenti
            users = conn.execute(
                text("""
                    SELECT id, phone FROM users 
                    WHERE id IN (:operator_id, :client_id)
                """),
                {
                    "operator_id": data["operator_id"],
                    "client_id": data["client_id"]
                }
            ).fetchall()

            if len(users) != 2:
                return jsonify({"error": "Operatore o cliente non valido"}), 400

            # Creazione appuntamento
            result = conn.execute(
                text("""
                    INSERT INTO appointments (operator_id, client_id, start_time, 
                                           end_time, service_type, created_at) 
                    VALUES (:operator_id, :client_id, :start_time, :end_time, 
                           :service_type, NOW())
                """),
                {
                    "operator_id": data["operator_id"],
                    "client_id": data["client_id"],
                    "start_time": datetime.fromisoformat(data["start_time"]),
                    "end_time": datetime.fromisoformat(data["end_time"]),
                    "service_type": data.get("service_type", "")
                }
            )
            conn.commit()

            # Notifica WhatsApp
            client_phone = next((u.phone for u in users if u.id == data["client_id"]), None)
            if client_phone:
                send_whatsapp_notification(
                    client_phone,
                    f"Nuovo appuntamento creato per il {data['start_time']}"
                )

            execution_time = time.time() - start_time
            app.logger.info(f"Appuntamento creato in {execution_time:.2f} secondi")

            return jsonify({"message": "Appuntamento creato con successo"}), 200

    except Exception as e:
        app.logger.error(f"Errore creazione appuntamento: {str(e)}")
        return jsonify({"error": "Errore durante la creazione dell'appuntamento"}), 500

@app.route("/api/admin/appointments/<int:appointment_id>", methods=["PUT", "DELETE"])
def manage_appointment_by_id(appointment_id):
    """
    Gestione appuntamento ottimizzata
    """
    try:
        with db.engine.connect().execution_options(timeout=5) as conn:
            # Verifica esistenza appuntamento
            appo = conn.execute(
                text("SELECT id FROM appointments WHERE id = :id"),
                {"id": appointment_id}
            ).fetchone()

            if not appo:
                return jsonify({"error": "Appuntamento non trovato"}), 404

            if request.method == "DELETE":
                conn.execute(
                    text("DELETE FROM appointments WHERE id = :id"),
                    {"id": appointment_id}
                )
                conn.commit()
                return jsonify({"message": "Appuntamento eliminato"}), 200

            data = request.get_json()
            update_fields = []
            params = {"id": appointment_id}

            if "start_time" in data:
                update_fields.append("start_time = :start_time")
                params["start_time"] = datetime.fromisoformat(data["start_time"])
            if "end_time" in data:
                update_fields.append("end_time = :end_time")
                params["end_time"] = datetime.fromisoformat(data["end_time"])
            if "service_type" in data:
                update_fields.append("service_type = :service_type")
                params["service_type"] = data["service_type"]
            if "status" in data:
                update_fields.append("status = :status")
                params["status"] = data["status"]

            if update_fields:
                query = f"UPDATE appointments SET {', '.join(update_fields)} WHERE id = :id"
                conn.execute(text(query), params)
                conn.commit()

            return jsonify({"message": "Appuntamento aggiornato"}), 200

    except Exception as e:
        app.logger.error(f"Errore gestione appuntamento: {str(e)}")
        return jsonify({"error": "Errore durante la gestione dell'appuntamento"}), 500

@app.route("/api/admin/send-reminders", methods=["POST"])
def send_reminders():
    """
    Invio reminder ottimizzato
    """
    try:
        start_time = time.time()
        tomorrow = datetime.now() + timedelta(days=1)
        start_tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end_tomorrow = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

        with db.engine.connect().execution_options(timeout=5) as conn:
            # Query ottimizzata per appuntamenti e clienti
            results = conn.execute(
                text("""
                    SELECT a.start_time, u.phone
                    FROM appointments a
                    JOIN users u ON a.client_id = u.id
                    WHERE a.start_time BETWEEN :start AND :end
                    AND u.phone IS NOT NULL
                """),
                {
                    "start": start_tomorrow,
                    "end": end_tomorrow
                }
            ).fetchall()

            for result in results:
                send_whatsapp_notification(
                    result.phone,
                    f"Reminder: hai un appuntamento domani alle {result.start_time.strftime('%H:%M')}"
                )

        execution_time = time.time() - start_time
        app.logger.info(f"Reminder inviati in {execution_time:.2f} secondi")
        return jsonify({"message": "Notifiche inviate"}), 200

    except Exception as e:
        app.logger.error(f"Errore invio reminder: {str(e)}")
        return jsonify({"error": "Errore durante l'invio dei reminder"}), 500

##############################################################################
# GESTIONE SLOT PENDING (ADMIN)
##############################################################################
@app.route("/api/admin/slots/pending", methods=["GET"])
def get_pending_slots():
    """
    Lista slot pending ottimizzata
    """
    try:
        with db.engine.connect().execution_options(timeout=5) as conn:
            slots = conn.execute(
                text("""
                    SELECT id, operator_id, client_id, day_of_week, 
                           start_time, end_time, status
                    FROM slots 
                    WHERE status = 'pending'
                """)
            ).fetchall()

            return jsonify({
                "slots": [{
                    "id": s.id,
                    "operator_id": s.operator_id,
                    "client_id": s.client_id,
                    "day_of_week": s.day_of_week,
                    "start_time": s.start_time.strftime("%H:%M"),
                    "end_time": s.end_time.strftime("%H:%M"),
                    "status": s.status,
                } for s in slots]
            }), 200

    except Exception as e:
        app.logger.error(f"Errore recupero slot pending: {str(e)}")
        return jsonify({"error": "Errore durante il recupero degli slot pending"}), 500

@app.route("/api/admin/slots/<int:slot_id>/approve", methods=["PUT"])
def approve_slot(slot_id):
    """
    Approvazione slot ottimizzata
    """
    try:
        with db.engine.connect().execution_options(timeout=5) as conn:
            result = conn.execute(
                text("""
                    UPDATE slots 
                    SET status = 'approved' 
                    WHERE id = :slot_id
                    AND status = 'pending'
                """),
                {"slot_id": slot_id}
            )
            conn.commit()

            if result.rowcount == 0:
                return jsonify({"error": "Slot non trovato o non in stato pending"}), 404

            return jsonify({"message": "Slot approvato con successo"}), 200

    except Exception as e:
        app.logger.error(f"Errore approvazione slot: {str(e)}")
        return jsonify({"error": "Errore durante l'approvazione dello slot"}), 500

@app.route("/api/admin/slots/<int:slot_id>/reject", methods=["PUT"])
def reject_slot(slot_id):
    """
    Rifiuto slot ottimizzato
    """
    try:
        with db.engine.connect().execution_options(timeout=5) as conn:
            result = conn.execute(
                text("""
                    UPDATE slots 
                    SET status = 'rejected' 
                    WHERE id = :slot_id
                    AND status = 'pending'
                """),
                {"slot_id": slot_id}
            )
            conn.commit()

            if result.rowcount == 0:
                return jsonify({"error": "Slot non trovato o non in stato pending"}), 404

            return jsonify({"message": "Slot rifiutato"}), 200

    except Exception as e:
        app.logger.error(f"Errore rifiuto slot: {str(e)}")
        return jsonify({"error": "Errore durante il rifiuto dello slot"}), 500

##############################################################################
# CLIENT: RICHIESTA SLOT
##############################################################################
@app.route("/api/client/slots/request", methods=["POST"])
def request_slot():
    """
    Richiesta slot ottimizzata
    """
    try:
        start_time = time.time()
        data = request.get_json()

        with db.engine.connect().execution_options(timeout=5) as conn:
            # Verifica esistenza utenti
            users = conn.execute(
                text("""
                    SELECT id FROM users 
                    WHERE id IN (:client_id, :operator_id)
                """),
                {
                    "client_id": data["client_id"],
                    "operator_id": data["operator_id"]
                }
            ).fetchall()

            if len(users) != 2:
                return jsonify({"error": "Client o operator non valido"}), 400

            # Creazione slot
            result = conn.execute(
                text("""
                    INSERT INTO slots (operator_id, client_id, day_of_week, 
                                    start_time, end_time, status, is_active, created_at)
                    VALUES (:operator_id, :client_id, :day_of_week, :start_time, 
                            :end_time, 'pending', TRUE, NOW())
                """),
                {
                    "operator_id": data["operator_id"],
                    "client_id": data["client_id"],
                    "day_of_week": int(data["day_of_week"]),
                    "start_time": datetime.strptime(data["start_time"], "%H:%M").time(),
                    "end_time": datetime.strptime(data["end_time"], "%H:%M").time()
                }
            )
            conn.commit()

            execution_time = time.time() - start_time
            app.logger.info(f"Slot richiesto in {execution_time:.2f} secondi")

            return jsonify({"message": "Richiesta slot inviata"}), 201

    except Exception as e:
        app.logger.error(f"Errore richiesta slot: {str(e)}")
        return jsonify({"error": "Errore durante la richiesta dello slot"}), 500

##############################################################################
# MAIN
##############################################################################
if __name__ == "__main__":
    # Crea le tabelle nel DB (se non esistono)
    with app.app_context():
        try:
            db.create_all()
            print("Database inizializzato con successo")
        except Exception as e:
            print(f"Errore inizializzazione database: {e}")

    print(">>> Avvio server Flask su http://localhost:5000")
    app.run(debug=True, port=5000)
