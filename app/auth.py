from flask import Blueprint, request, jsonify, make_response, session
from flask_login import current_user, login_user, login_required, logout_user
from flask_cors import cross_origin
from flask_mail import Message
from app import mail;
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

confirmation_codes = {}

def store_confirmation_code(code, email):
    confirmation_codes[email] = {'confirmation_code': code, 'confirmation_code_expiry': time.time() + 300}

def verify_confirmation_code(email, code):
    # Check if email and code are provided
    if not email or not code:
        return False, "Email and confirmation code are required."

    # Check if the email exists in the confirmation_codes
    if email not in confirmation_codes:
        return False, "Confirmation code not found for this email."

    # Get the stored confirmation code and expiry
    stored_data = confirmation_codes[email]

    # Check if the code has expired
    if time.time() > stored_data.get("confirmation_code_expiry", 0):
        delete_confirmation_code(email)
        return False, "Confirmation code has expired."

    # Check if the code matches
    if code == stored_data.get('confirmation_code'):
        delete_confirmation_code(email)  # Optionally delete after success
        return True, None  # Successfully verified

    return False, "Invalid confirmation code."
    
def delete_confirmation_code(email):
    if email in confirmation_codes:
        del confirmation_codes[email]


# ROUTES FOR ALL USERS

@auth.route('/csrf-token', methods=['GET'])
def csrf_token():
    """Generate and send the CSRF token."""
    token = generate_csrf()
    response = make_response(jsonify({"message": "CSRF token set", "csrf_token": token}))
    response.set_cookie(
        'csrf_token', token, httponly=False, secure=True, samesite='None'
    )
    return response

# ROUTES FOR GUEST USERS

#Check username availability
@auth.route("/check-username/<string:username>", methods=['GET'])
@cross_origin(supports_credentials=True)
def check_username(username):
    if not username:
        return jsonify({"message": "No username provided"})
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "This username hasn't been taken yet"})
    else:
        return jsonify({"message": "This username is already taken"}) 
    
@auth.route('/register', methods=['POST'])
@cross_origin(supports_credentials=True)
def register():
    try:
        validate_request_csrf()
        data = request.get_json()

        # Validate confirmation code
        # confirmed = check_confirmation_code(data.get('confirmation_code'), session.get('confirmation_code'), session.get('confirmation_code_expiry'))
        # if not confirmed:
        #     return jsonify({'message': 'Invalid or expired confirmation code'}), 400
        
        # Validate required fields for all users
        required_fields = ['email', 'confirmation_code', 'username', 'password', "full_name", "address", "card_number"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
    
        email = data['email']
        confirmation_code  = data["confirmation_code"]
        confirmed, message = verify_confirmation_code(confirmation_code, email)
        if not confirmed:
            return jsonify({"message": message}), 400
        
        username = data['username']
        password = data['password']
        role = "buyer"
        full_name = data['full_name']
        address = data['address']
        card_number = data['card_number']

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
def send_confirmation_code():
    validate_request_csrf()
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Generate a random OTP
    otp = random.randint(100000, 999999)

    # Store OTP and email with timestamp
    store_confirmation_code(otp, email)

    # Send code to email 
    subject = "Confirmation code"
    body = f"Your GeorgeHub Shopping confirmation code: {otp}. If you didn't ask for it, " \
    "it means that somebody else is trying to use your email for registration at " \
    "GeorgeHub Shopping or reset a password for this email."

    if not subject or not body:
        return jsonify({"error": "Missing fields"}), 400

    msg = Message(subject,
                  recipients=[email],
                  body=body)
    try:
        mail.send(msg)
        return jsonify({"message": "Email sent successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    email = data.get('email') or current_user.email

    # Validate confirmation code
    confirmed, message = verify_confirmation_code(data.get('confirmation_code'), email)
    if not confirmed:
        return jsonify({'message': message}), 400
    
    username = data.get('username') or current_user.username
    password = data.get('password') or current_user.password
    role = data.get('role') or current_user.role
    if role not in ['buyer', 'seller']:
        return jsonify({'message': 'Invalid role'}), 400
    
    full_name = data.get('full_name') or current_user.full_name
    address = data.get('address') or current_user.address
    card_number = data.get('card_number') or current_user.card_number
    support_email = data.get('support_email') or current_user.support_email
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
    user.support_email = support_email

    db.session.commit()

    return jsonify({
        'message': 'User updated to successfully!',
        'user': {
            'email': email,
            'role': role,
            'full_name': full_name,
            'address': address,
            'card_number': card_number,
            'support_email': support_email
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
