from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text  # Importa text da SQLAlchemy
import os

app = Flask(__name__)

# Configurazione del database
db_user = os.getenv("DB_USER", "root")  # Il tuo username MySQL
db_password = os.getenv("DB_PASSWORD", "lollo201416")  # La tua password MySQL
db_host = os.getenv("DB_HOST", "34.17.85.107")  # L'hostname del database
db_name = os.getenv("DB_NAME", "appointment_db")  # Nome del database

# Stringa di connessione
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "chiave_super_segreta_123")

# Inizializzazione del database
db = SQLAlchemy(app)

# Configura i domini consentiti per le richieste (CORS)
CORS(
    app,
    resources={r"/*": {"origins": "https://appo-wjc5-kxhff1ws8-andreasettannis-projects.vercel.app"}},
)

# Test della connessione
@app.route("/")
def index():
    return "Flask è in esecuzione!"

if __name__ == "__main__":
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))  # Usa text() per la query
        print("Connessione al database riuscita!")
    except Exception as e:
        print(f"Errore durante la connessione al database: {e}")

    app.run(debug=True)
