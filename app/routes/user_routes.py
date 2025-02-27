from flask import jsonify, request, abort
from flask_login import login_required, current_user
from ..models import db, User
from . import category_bp as main

# A route for getting public information about a single user
@main.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    public_data = {
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "support_email": user.support_email or None,   
    }
    return jsonify(public_data), 200


