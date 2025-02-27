from flask import jsonify, request, abort
from flask_login import login_required, current_user
from ..models import db, Category
from . import category_bp as main

@main.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{
        'id': c.id,
        'title': c.title
    } for c in categories])

@main.route('/categories', methods=['POST'])
@login_required
def create_category():
    if not current_user.is_admin():
        abort(403)
    
    data = request.get_json()
    category = Category(title=data['title'])
    db.session.add(category)
    db.session.commit()
    return jsonify({'message': 'Category created', 'id': category.id}), 201
