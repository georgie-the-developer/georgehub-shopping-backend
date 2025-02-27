from flask import jsonify, request, abort
from flask_login import login_required, current_user
from ..models import db, BannedEmail, User, Product, Category
from . import category_bp as main

# USER MANAGEMENT ROUTES

# Get general information about all users for admin dashboard

@main.route('/admin/users', methods=['GET'])
@login_required
def get_users():
    if not current_user.is_admin():
        abort(403)
    
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'role': user.role,
        'full_name': user.full_name,
    } for user in users])

# User full profile for admins

@main.route('/admin/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    if not current_user.is_admin():
        abort(403)
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200

# Delete a user, ban their email

@main.route('/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        abort(403)
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    banned_email = BannedEmail(email=user.email)

    db.session.add(banned_email)
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted, email banned'}), 200




