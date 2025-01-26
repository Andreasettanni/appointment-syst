from flask import Blueprint, request, jsonify
from app.models import Operator, User
from app import db

bp = Blueprint('operators', __name__, url_prefix='/api/operators')

@bp.route('/', methods=['GET'])
def get_operators():
    operators = Operator.query.all()
    return jsonify([{
        'id': op.id,
        'admin_id': op.admin_id,
        'specialization': op.specialization,
        'user': {
            'username': op.user.username,
            'email': op.user.email
        }
    } for op in operators]), 200

@bp.route('/', methods=['POST'])
def create_operator():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('user_id', 'admin_id', 'specialization')):
        return jsonify({'error': 'Missing required fields'}), 400
        
    operator = Operator(
        id=data['user_id'],
        admin_id=data['admin_id'],
        specialization=data['specialization']
    )
    
    db.session.add(operator)
    db.session.commit()
    
    return jsonify({'message': 'Operator created successfully'}), 201