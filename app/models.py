from . import db
import time

def get_current_timestamp():
    return int(time.time() * 1000)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    card_number = db.Column(db.String(255), nullable=True)
    support_email = db.Column(db.String(120), nullable=True)
    products = db.relationship('Product', backref='user', lazy=True)
    # reviews = db.relationship('Review', backref='product', lazy=True) # This line is not needed for now

    def __init__(self, email, username, password, role, full_name=None, address=None, card_number=None, support_email=None):
        self.email = email
        self.username = username
        self.password = password
        self.role = role
        self.full_name = full_name
        self.address = address
        self.card_number = card_number
        self.support_email = support_email
    # These methods are required for Flask-Login to work properly
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    def is_seller(self):
        return self.role == 'seller'

    def is_buyer(self):
        return self.role == 'buyer'

    def is_admin(self):
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'full_name': self.full_name,
            'address': self.address,
            'card_number': self.card_number,
            'support_email': self.support_email
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    images = db.Column(db.JSON, nullable=True)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False)
    overall_rating = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.Integer, default=get_current_timestamp)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviews = db.relationship('Review', backref='product', lazy=True)

    def update_stock(self, quantity):
        """Update stock quantity and return success status"""
        if self.stock_quantity + quantity >= 0:
            self.stock_quantity += quantity
            return True
        return False

    def calculate_rating(self):
        """Calculate and update overall rating from reviews"""
        if not self.reviews:
            return 0
        self.overall_rating = sum(review.rating for review in self.reviews) / len(self.reviews)
        return self.overall_rating

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.Integer, default=get_current_timestamp)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 

class BannedEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)