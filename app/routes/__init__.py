from flask import Blueprint

# Create blueprints
product_bp = Blueprint('product', __name__)
category_bp = Blueprint('category', __name__)
review_bp = Blueprint('review', __name__)
admin_bp = Blueprint('admin', __name__)

# Import routes
from . import product_routes
from . import category_routes
from . import review_routes
from . import admin_routes

# List all blueprints to register
blueprints = [product_bp, category_bp, review_bp, admin_bp]
# thanks again
# no i now how to do it now
# thanks. I will try it out