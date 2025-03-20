from flask import Blueprint, request, jsonify, make_response, session
from flask_login import current_user, login_user, login_required, logout_user
from flask_cors import cross_origin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
from flask_wtf.csrf import generate_csrf, validate_csrf, ValidationError
import random
import time

auth = Blueprint('auth', __name__)

def validate_request_csrf():
    try:
        csrf_token = request.headers.get('Cookies').split('csrf_token=')[1]
        print(csrf_token)
        if not csrf_token:
            return jsonify({"message": "No CSRF token provided"}), 401
        # Validate the CSRF token
        validate_csrf(csrf_token)
    except ValidationError:
        # CSRF validation failed, possibly due to expired session
        return jsonify({"message": "CSRF token invalid or session expired"}), 401
    except Exception as e:
        # Handle any other exceptions
        return jsonify({"message": "CSRF validation failed", "error": str(e)}), 401

def is_admin():
    return current_user.role == 'admin'

def is_seller():
    return current_user.role == 'seller'

def is_buyer():
    return current_user.role == 'buyer'

def store_confirmation_code(code):
    session['confirmation_code'] = code
    session['confirmation_code_expiry'] = time.time() + 300  # 5 minutes

def check_confirmation_code(code, stored_code, expiry_time = 0):
    if time.time() > expiry_time:
        return False
    if not stored_code or stored_code == "":
        return False
    return code == stored_code

def delete_confirmation_code():
    session.pop('confirmation_code', None)
    session.pop('confirmation_code_expiry', None)


# ROUTES FOR ALL USERS

@auth.route('/csrf-token', methods=['GET'])
def csrf_token():
    """Generate and send the CSRF token."""
    token = generate_csrf()
    response = make_response(jsonify({"message": "CSRF token set"}))
    response.set_cookie(
        'csrf_token', token, httponly=False, secure=True, samesite='None'
    )
    return response

# ROUTES FOR GUEST USERS

@auth.route('/register', methods=['POST'])
@cross_origin(supports_credentials=True)
def register():
    try:
        validate_request_csrf()
        data = request.get_json()

        # Validate confirmation code
        confirmed = check_confirmation_code(data.get('confirmation_code'), session.get('confirmation_code'), session.get('confirmation_code_expiry'))
        if not confirmed:
            return jsonify({'message': 'Invalid or expired confirmation code'}), 400
        
        # Validate required fields for all users
        required_fields = ['email', 'username', 'password', 'password_confirm', "full_name", "address", "card_number"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400

        email = data['email']
        username = data['username']
        password = data['password']
        password_confirm = data['password_confirm']
        role = "buyer"
        full_name = data['full_name']
        address = data['address']
        card_number = data['card_number']
        support_email = data['support_email'] or None
        # Check password confirmation
        if password != password_confirm:
            return jsonify({'message': 'Passwords do not match'}), 400

        # Check existing email/username
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'Email already exists'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'message': 'Username already exists'}), 400

        # Create new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            email=email,
            username=username,
            password=hashed_password,
            role=role,
            full_name=full_name,
            address=address,
            card_number=card_number,
            support_email=support_email
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)

        return jsonify({
            'message': 'Account created successfully!',
            'user': {
                'email': email,
                'username': username,
                'role': role,
                'full_name': full_name,
                "address": address,
                "card_number": card_number
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@auth.route('/login', methods=['POST'])
@cross_origin(supports_credentials=True)
def login():
    try:
        validate_request_csrf()
        data = request.get_json()
        username = data.get('username') or False
        email = data.get('email') or False
        password = data.get('password') or False
        # Validate required fields
        if (not username and not email) or not password:
            return jsonify({'message': 'Username or email and password are required'}), 400
        
        if not username:
            user = User.query.filter_by(email=email).first()
        else:
            user = User.query.filter_by(username=username).first()
        
        if not user.email or not check_password_hash(user.password, password):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        login_user(user, remember=True)
        return jsonify({
            'message': 'Login successful!',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': user.role,
                'full_name': user.full_name,
                'address': user.address,
                'card_number': user.card_number
            }
        }), 200

    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@auth.route('/confirmation-code', methods=['POST'])
@cross_origin(supports_credentials=True)
@login_required
def send_confirmation_code():

    validate_request_csrf()

    user = User.query.filter_by(id=current_user.id).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    
    confirmation_code = str(random.randint(1000, 9999))
    store_confirmation_code(confirmation_code)

    # TODO: Send `confirmation_code` via email/SMS (implement actual sending logic)
    print(f"Confirmation code for {current_user.email}: {confirmation_code}")  # Debugging only

    return jsonify({'message': 'Confirmation code sent successfully!'}), 200

# ROUTES FOR REGISTERED USERS

@auth.route('/me', methods=['GET'])
@login_required
@cross_origin(supports_credentials=True)
def me():
    try:
        return jsonify({
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'username': current_user.username,
                'role': current_user.role,
                'full_name': current_user.full_name if current_user.role in ['buyer', 'seller'] else None,
                'address': current_user.address if current_user.role in ['buyer', 'seller'] else None,
                'card_number': current_user.card_number if current_user.role in ['buyer', 'seller'] else None
            }
        }), 200
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@auth.route('/me', methods=['PUT'])
@cross_origin(supports_credentials=True)
@login_required
def update_user():
    validate_request_csrf()

    data = request.get_json()

    # Validate confirmation code
    confirmed = check_confirmation_code(data.get('confirmation_code'), session.get('confirmation_code'), session.get('confirmation_code_expiry'))
    if not confirmed:
        return jsonify({'message': 'Invalid or expired confirmation code'}), 400
    
    email = data.get('email') or current_user.email
    username = data.get('username') or current_user.username
    password = data.get('password') or current_user.password
    role = data.get('role') or current_user.role
    if role not in ['buyer', 'seller']:
        return jsonify({'message': 'Invalid role'}), 400
    
    full_name = data.get('full_name') or current_user.full_name
    address = data.get('address') or current_user.address
    card_number = data.get('card_number') or current_user.card_number

    user = User.query.filter_by(id=current_user.id).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    user.email = email
    user.username = username
    user.password = generate_password_hash(password, method='pbkdf2:sha256')
    user.role = role
    user.address = address
    user.full_name = full_name
    user.card_number = card_number

    db.session.commit()

    return jsonify({
        'message': 'User updated to successfully!',
        'user': {
            'email': email,
            'role': role,
            'full_name': full_name,
            'address': address,
            'card_number': card_number
        }
    }), 200

# Route for logout
@auth.route('/logout', methods=['POST'])
@login_required
@cross_origin(supports_credentials=True)
def logout():
    # Log out the user and clear session.
    logout_user()
    response = make_response(jsonify({"message": "Logout successful"}))
    return response