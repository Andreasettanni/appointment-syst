from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import time
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurazione database
DB_CONFIG = {
    "host": "34.17.85.107",
    "user": "root",
    "password": "lollo201416",
    "db": "appointment_db",
    "connect_timeout": 3,
    "read_timeout": 3,
    "write_timeout": 3
}

# Configurazione CORS
CORS(
    app,
    resources={r"/*": {"origins": [
        "http://localhost:3000",
        "https://clientappo.vercel.app",
        "https://appointment-syst.vercel.app",
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

def get_db():
    """Crea una nuova connessione al database"""
    try:
        logger.info("Tentativo di connessione al database...")
        conn = pymysql.connect(**DB_CONFIG)
        logger.info("Connessione al database riuscita")
        return conn
    except Exception as e:
        logger.error(f"Errore connessione database: {str(e)}")
        raise

@app.after_request
def add_cors_headers(response):
    """Aggiunge gli header CORS necessari"""
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
    
    logger.info(f"CORS headers aggiunti per {request.method} a {request.url}")
    return response

# Gestione OPTIONS per tutte le route
@app.route("/api/auth/register", methods=["OPTIONS"])
@app.route("/api/auth/login", methods=["OPTIONS"])
@app.route("/api/calendar/<int:user_id>", methods=["OPTIONS"])
@app.route("/api/admin/operators/<int:admin_id>", methods=["OPTIONS"])
@app.route("/api/admin/clients/<int:admin_id>", methods=["OPTIONS"])
def handle_preflight():
    response = jsonify({"message": "OK"})
    return response

@app.route("/")
def index_root():
    return "Server Flask attivo!"

@app.route("/api")
def index_api():
    return jsonify({"message": "Benvenuto nell'API!"})

@app.route("/api/auth/register", methods=["POST"])
def register():
    """Registrazione con timeout ridotto e gestione errori migliorata"""
    logger.info("Inizio registrazione")
    start_time = time.time()
    try:
        data = request.get_json()
        logger.info(f"Dati ricevuti: {data}")
        
        if not data:
            return jsonify({"error": "Dati mancanti"}), 400

        required = ["username", "password", "email"]
        if not all(field in data for field in required):
            return jsonify({"error": "Campi obbligatori mancanti"}), 400

        try:
            conn = get_db()
        except Exception as e:
            logger.error(f"Errore connessione DB: {str(e)}")
            return jsonify({"error": "Errore di connessione al database"}), 500

        try:
            with conn.cursor() as cursor:
                # Verifica duplicati
                cursor.execute("""
                    SELECT username FROM users 
                    WHERE username = %s OR email = %s
                    LIMIT 1
                """, (data["username"], data["email"]))
                
                if cursor.fetchone():
                    return jsonify({"error": "Username o email già esistenti"}), 400

                # Creazione utente
                hashed = generate_password_hash(data["password"], method="scrypt")
                cursor.execute("""
                    INSERT INTO users (username, password_hash, email, phone, role, admin_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    data["username"],
                    hashed,
                    data["email"],
                    data.get("phone", ""),
                    data.get("role", "client"),
                    data.get("admin_id")
                ))
                conn.commit()
                new_user_id = cursor.lastrowid

            logger.info(f"Registrazione completata in {time.time() - start_time:.2f} secondi")
            return jsonify({
                "message": "Registrazione completata",
                "user": {
                    "id": new_user_id,
                    "username": data["username"],
                    "email": data["email"],
                    "role": data.get("role", "client")
                }
            }), 201

        finally:
            conn.close()
            logger.info("Connessione database chiusa")

    except Exception as e:
        logger.error(f"Errore registrazione: {str(e)}")
        return jsonify({"error": "Errore durante la registrazione"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    """Login con timeout ridotto"""
    logger.info("Inizio login")
    start_time = time.time()
    try:
        data = request.get_json()
        logger.info(f"Dati login ricevuti: {data}")
        
        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "Credenziali mancanti"}), 400

        try:
            conn = get_db()
        except Exception as e:
            logger.error(f"Errore connessione DB: {str(e)}")
            return jsonify({"error": "Errore di connessione al database"}), 500

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, username, password_hash, email, role, admin_id, phone
                    FROM users 
                    WHERE username = %s
                    LIMIT 1
                """, (data["username"],))
                user = cursor.fetchone()

            if not user or not check_password_hash(user["password_hash"], data["password"]):
                return jsonify({"error": "Credenziali non valide"}), 401

            logger.info(f"Login completato in {time.time() - start_time:.2f} secondi")
            return jsonify({
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "admin_id": user["admin_id"],
                    "phone": user["phone"]
                }
            }), 200

        finally:
            conn.close()
            logger.info("Connessione database chiusa")

    except Exception as e:
        logger.error(f"Errore login: {str(e)}")
        return jsonify({"error": "Errore durante il login"}), 500

[... continuo con il resto del backend nella prossima parte ...]

# ... continua dal codice precedente ...

@app.route("/api/calendar/<int:user_id>", methods=["GET"])
def get_calendar_data(user_id):
    """Calendario ottimizzato con query dirette"""
    logger.info(f"Richiesta calendario per user_id: {user_id}")
    try:
        conn = get_db()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Ottieni ruolo utente
                cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user:
                    return jsonify({"error": "Utente non trovato"}), 404

                # Query ottimizzate per slot e appuntamenti
                if user['role'] == "admin":
                    cursor.execute("SELECT * FROM slots")
                    slots = cursor.fetchall()
                    cursor.execute("SELECT * FROM appointments")
                    appointments = cursor.fetchall()
                elif user['role'] == "operator":
                    cursor.execute("SELECT * FROM slots WHERE operator_id = %s", (user_id,))
                    slots = cursor.fetchall()
                    cursor.execute("SELECT * FROM appointments WHERE operator_id = %s", (user_id,))
                    appointments = cursor.fetchall()
                else:  # client
                    cursor.execute("SELECT * FROM slots WHERE status = 'approved'")
                    slots = cursor.fetchall()
                    cursor.execute("SELECT * FROM appointments WHERE client_id = %s", (user_id,))
                    appointments = cursor.fetchall()

                # Converti in eventi
                events = []
                now = datetime.now()

                # Processa slot
                for slot in slots:
                    cursor.execute("SELECT username FROM users WHERE id = %s", (slot['operator_id'],))
                    operator = cursor.fetchone()
                    
                    diff = slot['day_of_week'] - now.weekday()
                    if diff < 0:
                        diff += 7
                    base_date = now.date() + timedelta(days=diff)
                    start_dt = datetime.combine(base_date, slot['start_time'])
                    end_dt = datetime.combine(base_date, slot['end_time'])

                    events.append({
                        "type": "slot",
                        "id": f"slot-{slot['id']}",
                        "slot_id": slot['id'],
                        "operator_id": slot['operator_id'],
                        "operator_name": operator['username'] if operator else "???",
                        "start_time": start_dt.isoformat(),
                        "end_time": end_dt.isoformat(),
                        "status": slot['status']
                    })

                # Processa appuntamenti
                for appt in appointments:
                    cursor.execute("SELECT username FROM users WHERE id IN (%s, %s)", 
                                 (appt['client_id'], appt['operator_id']))
                    users = cursor.fetchall()
                    client = next((u for u in users if u['username']), {"username": "???"})
                    operator = next((u for u in users if u['username']), {"username": "???"})

                    events.append({
                        "type": "appointment",
                        "id": appt['id'],
                        "client_id": appt['client_id'],
                        "operator_id": appt['operator_id'],
                        "clientName": client['username'],
                        "operatorName": operator['username'],
                        "start_time": appt['start_time'].isoformat(),
                        "end_time": appt['end_time'].isoformat(),
                        "service_type": appt['service_type'],
                        "status": appt['status']
                    })

                return jsonify({"events": events}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore calendario: {str(e)}")
        return jsonify({"error": "Errore durante il recupero del calendario"}), 500

@app.route("/api/admin/operators/<int:admin_id>", methods=["GET"])
def get_operators(admin_id):
    """Lista operatori ottimizzata"""
    try:
        conn = get_db()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, username, email, phone, specialization 
                    FROM users 
                    WHERE admin_id = %s AND role = 'operator'
                """, (admin_id,))
                operators = cursor.fetchall()

                return jsonify({"operators": operators}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore recupero operatori: {str(e)}")
        return jsonify({"error": "Errore durante il recupero degli operatori"}), 500

@app.route("/api/admin/clients/<int:admin_id>", methods=["GET"])
def get_clients(admin_id):
    """Lista clienti ottimizzata"""
    try:
        conn = get_db()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Verifica admin
                cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'admin'", (admin_id,))
                admin = cursor.fetchone()
                if not admin:
                    return jsonify({"error": "Non autorizzato"}), 403

                cursor.execute("""
                    SELECT id, username, email, phone 
                    FROM users 
                    WHERE admin_id = %s AND role = 'client'
                """, (admin_id,))
                clients = cursor.fetchall()

                return jsonify({"clients": clients}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore recupero clienti: {str(e)}")
        return jsonify({"error": "Errore durante il recupero dei clienti"}), 500

@app.route("/api/admin/operators/add", methods=["POST"])
def add_operator():
    """Aggiunta operatore ottimizzata"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dati mancanti"}), 400

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # Verifica admin
                cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'admin'", 
                             (data['admin_id'],))
                if not cursor.fetchone():
                    return jsonify({"error": "Non autorizzato"}), 403

                # Verifica duplicati
                cursor.execute("""
                    SELECT username FROM users 
                    WHERE username = %s OR email = %s
                """, (data['username'], data['email']))
                if cursor.fetchone():
                    return jsonify({"error": "Username o email già esistenti"}), 400

                # Creazione operatore
                hashed = generate_password_hash(data['password'], method="scrypt")
                cursor.execute("""
                    INSERT INTO users (username, password_hash, email, phone, role, 
                                    admin_id, specialization) 
                    VALUES (%s, %s, %s, %s, 'operator', %s, %s)
                """, (
                    data['username'],
                    hashed,
                    data['email'],
                    data.get('phone', ''),
                    data['admin_id'],
                    data.get('specialization', '')
                ))
                conn.commit()

                return jsonify({"message": "Operatore creato con successo"}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore creazione operatore: {str(e)}")
        return jsonify({"error": "Errore durante la creazione dell'operatore"}), 500

[... continuo con il resto delle route nella prossima parte ...]

# ... continua dal codice precedente ...

@app.route("/api/calendar/<int:user_id>", methods=["GET"])
def get_calendar_data(user_id):
    """Calendario ottimizzato con query dirette"""
    logger.info(f"Richiesta calendario per user_id: {user_id}")
    try:
        conn = get_db()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Ottieni ruolo utente
                cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user:
                    return jsonify({"error": "Utente non trovato"}), 404

                # Query ottimizzate per slot e appuntamenti
                if user['role'] == "admin":
                    cursor.execute("SELECT * FROM slots")
                    slots = cursor.fetchall()
                    cursor.execute("SELECT * FROM appointments")
                    appointments = cursor.fetchall()
                elif user['role'] == "operator":
                    cursor.execute("SELECT * FROM slots WHERE operator_id = %s", (user_id,))
                    slots = cursor.fetchall()
                    cursor.execute("SELECT * FROM appointments WHERE operator_id = %s", (user_id,))
                    appointments = cursor.fetchall()
                else:  # client
                    cursor.execute("SELECT * FROM slots WHERE status = 'approved'")
                    slots = cursor.fetchall()
                    cursor.execute("SELECT * FROM appointments WHERE client_id = %s", (user_id,))
                    appointments = cursor.fetchall()

                # Converti in eventi
                events = []
                now = datetime.now()

                # Processa slot
                for slot in slots:
                    cursor.execute("SELECT username FROM users WHERE id = %s", (slot['operator_id'],))
                    operator = cursor.fetchone()
                    
                    diff = slot['day_of_week'] - now.weekday()
                    if diff < 0:
                        diff += 7
                    base_date = now.date() + timedelta(days=diff)
                    start_dt = datetime.combine(base_date, slot['start_time'])
                    end_dt = datetime.combine(base_date, slot['end_time'])

                    events.append({
                        "type": "slot",
                        "id": f"slot-{slot['id']}",
                        "slot_id": slot['id'],
                        "operator_id": slot['operator_id'],
                        "operator_name": operator['username'] if operator else "???",
                        "start_time": start_dt.isoformat(),
                        "end_time": end_dt.isoformat(),
                        "status": slot['status']
                    })

                # Processa appuntamenti
                for appt in appointments:
                    cursor.execute("SELECT username FROM users WHERE id IN (%s, %s)", 
                                 (appt['client_id'], appt['operator_id']))
                    users = cursor.fetchall()
                    client = next((u for u in users if u['username']), {"username": "???"})
                    operator = next((u for u in users if u['username']), {"username": "???"})

                    events.append({
                        "type": "appointment",
                        "id": appt['id'],
                        "client_id": appt['client_id'],
                        "operator_id": appt['operator_id'],
                        "clientName": client['username'],
                        "operatorName": operator['username'],
                        "start_time": appt['start_time'].isoformat(),
                        "end_time": appt['end_time'].isoformat(),
                        "service_type": appt['service_type'],
                        "status": appt['status']
                    })

                return jsonify({"events": events}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore calendario: {str(e)}")
        return jsonify({"error": "Errore durante il recupero del calendario"}), 500

@app.route("/api/admin/operators/<int:admin_id>", methods=["GET"])
def get_operators(admin_id):
    """Lista operatori ottimizzata"""
    try:
        conn = get_db()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, username, email, phone, specialization 
                    FROM users 
                    WHERE admin_id = %s AND role = 'operator'
                """, (admin_id,))
                operators = cursor.fetchall()

                return jsonify({"operators": operators}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore recupero operatori: {str(e)}")
        return jsonify({"error": "Errore durante il recupero degli operatori"}), 500

@app.route("/api/admin/clients/<int:admin_id>", methods=["GET"])
def get_clients(admin_id):
    """Lista clienti ottimizzata"""
    try:
        conn = get_db()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Verifica admin
                cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'admin'", (admin_id,))
                admin = cursor.fetchone()
                if not admin:
                    return jsonify({"error": "Non autorizzato"}), 403

                cursor.execute("""
                    SELECT id, username, email, phone 
                    FROM users 
                    WHERE admin_id = %s AND role = 'client'
                """, (admin_id,))
                clients = cursor.fetchall()

                return jsonify({"clients": clients}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore recupero clienti: {str(e)}")
        return jsonify({"error": "Errore durante il recupero dei clienti"}), 500

@app.route("/api/admin/operators/add", methods=["POST"])
def add_operator():
    """Aggiunta operatore ottimizzata"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dati mancanti"}), 400

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # Verifica admin
                cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'admin'", 
                             (data['admin_id'],))
                if not cursor.fetchone():
                    return jsonify({"error": "Non autorizzato"}), 403

                # Verifica duplicati
                cursor.execute("""
                    SELECT username FROM users 
                    WHERE username = %s OR email = %s
                """, (data['username'], data['email']))
                if cursor.fetchone():
                    return jsonify({"error": "Username o email già esistenti"}), 400

                # Creazione operatore
                hashed = generate_password_hash(data['password'], method="scrypt")
                cursor.execute("""
                    INSERT INTO users (username, password_hash, email, phone, role, 
                                    admin_id, specialization) 
                    VALUES (%s, %s, %s, %s, 'operator', %s, %s)
                """, (
                    data['username'],
                    hashed,
                    data['email'],
                    data.get('phone', ''),
                    data['admin_id'],
                    data.get('specialization', '')
                ))
                conn.commit()

                return jsonify({"message": "Operatore creato con successo"}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore creazione operatore: {str(e)}")
        return jsonify({"error": "Errore durante la creazione dell'operatore"}), 500

[... continuo con il resto delle route nella prossima parte ...]

@app.route("/api/admin/appointments", methods=["POST"])
def add_appointment():
    """Creazione appuntamento ottimizzata"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dati mancanti"}), 400

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # Verifica esistenza utenti
                cursor.execute("""
                    SELECT id, phone FROM users 
                    WHERE id IN (%s, %s)
                """, (data['operator_id'], data['client_id']))
                users = cursor.fetchall()

                if len(users) != 2:
                    return jsonify({"error": "Operatore o cliente non valido"}), 400

                # Creazione appuntamento
                cursor.execute("""
                    INSERT INTO appointments (operator_id, client_id, start_time, 
                                           end_time, service_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (
                    data['operator_id'],
                    data['client_id'],
                    data['start_time'],
                    data['end_time'],
                    data.get('service_type', '')
                ))
                conn.commit()

                # Notifica WhatsApp (simulata)
                client_phone = next((row[1] for row in users if row[0] == data['client_id']), None)
                if client_phone:
                    logger.info(f"[FAKE] Invio WhatsApp a {client_phone}: Nuovo appuntamento creato per il {data['start_time']}")

                return jsonify({"message": "Appuntamento creato con successo"}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore creazione appuntamento: {str(e)}")
        return jsonify({"error": "Errore durante la creazione dell'appuntamento"}), 500

@app.route("/api/admin/appointments/<int:appointment_id>", methods=["PUT", "DELETE"])
def manage_appointment_by_id(appointment_id):
    """Gestione appuntamento ottimizzata"""
    try:
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # Verifica esistenza appuntamento
                cursor.execute("SELECT id FROM appointments WHERE id = %s", (appointment_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Appuntamento non trovato"}), 404

                if request.method == "DELETE":
                    cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
                    conn.commit()
                    return jsonify({"message": "Appuntamento eliminato"}), 200

                data = request.get_json()
                updates = []
                params = []

                if 'start_time' in data:
                    updates.append("start_time = %s")
                    params.append(data['start_time'])
                if 'end_time' in data:
                    updates.append("end_time = %s")
                    params.append(data['end_time'])
                if 'service_type' in data:
                    updates.append("service_type = %s")
                    params.append(data['service_type'])
                if 'status' in data:
                    updates.append("status = %s")
                    params.append(data['status'])

                if updates:
                    query = f"UPDATE appointments SET {', '.join(updates)} WHERE id = %s"
                    params.append(appointment_id)
                    cursor.execute(query, tuple(params))
                    conn.commit()

                return jsonify({"message": "Appuntamento aggiornato"}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore gestione appuntamento: {str(e)}")
        return jsonify({"error": "Errore durante la gestione dell'appuntamento"}), 500

@app.route("/api/admin/send-reminders", methods=["POST"])
def send_reminders():
    """Invio reminder ottimizzato"""
    try:
        tomorrow = datetime.now() + timedelta(days=1)
        start_tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end_tomorrow = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

        conn = get_db()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT a.start_time, u.phone
                    FROM appointments a
                    JOIN users u ON a.client_id = u.id
                    WHERE a.start_time BETWEEN %s AND %s
                    AND u.phone IS NOT NULL
                """, (start_tomorrow, end_tomorrow))
                appointments = cursor.fetchall()

                for appt in appointments:
                    logger.info(f"[FAKE] Invio reminder WhatsApp a {appt['phone']}: Appuntamento domani alle {appt['start_time'].strftime('%H:%M')}")

                return jsonify({"message": "Notifiche inviate"}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore invio reminder: {str(e)}")
        return jsonify({"error": "Errore durante l'invio dei reminder"}), 500

@app.route("/api/admin/slots/pending", methods=["GET"])
def get_pending_slots():
    """Lista slot pending ottimizzata"""
    try:
        conn = get_db()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, operator_id, client_id, day_of_week, 
                           start_time, end_time, status
                    FROM slots 
                    WHERE status = 'pending'
                """)
                slots = cursor.fetchall()

                return jsonify({
                    "slots": [{
                        **slot,
                        "start_time": slot['start_time'].strftime("%H:%M"),
                        "end_time": slot['end_time'].strftime("%H:%M")
                    } for slot in slots]
                }), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore recupero slot pending: {str(e)}")
        return jsonify({"error": "Errore durante il recupero degli slot pending"}), 500

@app.route("/api/admin/slots/<int:slot_id>/<string:action>", methods=["PUT"])
def manage_slot(slot_id, action):
    """Gestione slot ottimizzata"""
    if action not in ['approve', 'reject']:
        return jsonify({"error": "Azione non valida"}), 400

    try:
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE slots 
                    SET status = %s 
                    WHERE id = %s AND status = 'pending'
                """, ('approved' if action == 'approve' else 'rejected', slot_id))
                conn.commit()

                if cursor.rowcount == 0:
                    return jsonify({"error": "Slot non trovato o non in stato pending"}), 404

                return jsonify({"message": f"Slot {action}d con successo"}), 200

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore gestione slot: {str(e)}")
        return jsonify({"error": f"Errore durante {action} dello slot"}), 500

@app.route("/api/client/slots/request", methods=["POST"])
def request_slot():
    """Richiesta slot ottimizzata"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dati mancanti"}), 400

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # Verifica esistenza utenti
                cursor.execute("""
                    SELECT id FROM users 
                    WHERE id IN (%s, %s)
                """, (data['client_id'], data['operator_id']))
                if len(cursor.fetchall()) != 2:
                    return jsonify({"error": "Client o operator non valido"}), 400

                # Creazione slot
                cursor.execute("""
                    INSERT INTO slots (operator_id, client_id, day_of_week, 
                                    start_time, end_time, status, is_active)
                    VALUES (%s, %s, %s, %s, %s, 'pending', TRUE)
                """, (
                    data['operator_id'],
                    data['client_id'],
                    int(data['day_of_week']),
                    data['start_time'],
                    data['end_time']
                ))
                conn.commit()

                return jsonify({"message": "Richiesta slot inviata"}), 201

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Errore richiesta slot: {str(e)}")
        return jsonify({"error": "Errore durante la richiesta dello slot"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
