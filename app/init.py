# app/__init__.py
from flask import Flask
from flask_cors import CORS
from config import Config
from app.extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inizializza le estensioni
    CORS(app)
    db.init_app(app)
    
    # Importa i modelli
    from app.models import User, Appointment, Slot
    
    # Importa e registra i blueprint
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    # Crea le tabelle del database
    with app.app_context():
        db.create_all()
    
    return app