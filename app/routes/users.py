from flask import Blueprint, jsonify
from app.models.user import User
from flask_cors import cross_origin

users_bp = Blueprint('users', __name__)

@users_bp.route('/api/users/admins', methods=['GET'])
@cross_origin()
def get_admins():
    """
    Ritorna la lista di utenti che hanno role='admin'
    """
    try:
        admins = User.query.filter_by(role='admin').all()
        admin_list = []
        for adm in admins:
            admin_list.append({
                'id': adm.id,
                'username': adm.username
            })
        return jsonify({'admins': admin_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
