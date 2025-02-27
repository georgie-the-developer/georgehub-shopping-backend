from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os
from datetime import timedelta
# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOADS_FOLDER'] = os.getenv('UPLOADS_FOLDER')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit to 16MB
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    csrf = CSRFProtect(app)

    # Restrict access to frontend
    CORS(app, origins=[os.getenv('ALLOWED_ORIGIN')], supports_credentials=True)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)

    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(weeks=1)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(weeks=1)
    # Import the User model here
    from app.models import User
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    login_manager.login_view = None  # Disable redirect

    # Register blueprints
    from .routes import blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint, url_prefix='/api')
    from .auth import auth
    app.register_blueprint(auth, url_prefix='/auth')
    print(f"DATABASE_URI: {os.getenv('SQLALCHEMY_DATABASE_URI')}")
    return app
