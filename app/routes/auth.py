from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User  # Assicurati che il percorso sia corretto
from app.extensions import db  # Assicurati che il percorso sia corretto
from flask_cors import cross_origin
import re  # Per la validazione dell'email

auth_bp = Blueprint('auth', __name__)

# Funzione per validare l'email
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

@auth_bp.route('/api/auth/register', methods=['POST'])
@cross_origin()
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dati non forniti'}), 400

    # Verifica campi obbligatori
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Campo obbligatorio mancante: {field}'}), 400

    # Validazione email
    if not is_valid_email(data['email']):
        return jsonify({'error': 'Email non valida'}), 400

    # Verifica se username o email già esistenti
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username già esistente'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email già esistente'}), 400

    # Genera hash della password
    hashed_password = generate_password_hash(data['password'], method='scrypt')

    # Crea nuovo utente
    try:
        new_user = User(
            username=data['username'],
            password_hash=hashed_password,
            email=data['email'],
            phone=data.get('phone', ''),  # Campo opzionale
            role=data.get('role', 'client')  # Default a 'client' se non specificato
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

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Errore durante la registrazione: {str(e)}'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
@cross_origin()
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dati non forniti'}), 400

    # Verifica campi obbligatori
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Campo obbligatorio mancante: {field}'}), 400

    # Trova l'utente
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'error': 'Credenziali non valide'}), 401

    # Verifica la password
    if check_password_hash(user.password_hash, data['password']):
        return jsonify({
            'message': 'Login effettuato con successo',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'phone': user.phone,
                'admin_id': user.admin_id
            }
        }), 200

    return jsonify({'error': 'Credenziali non valide'}), 401