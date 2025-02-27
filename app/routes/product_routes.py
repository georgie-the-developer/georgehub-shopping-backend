from flask import jsonify, request, abort, send_from_directory, url_for
from flask_login import login_required, current_user
from ..models import db, Product, Category
from . import product_bp as main
from ..utils.file_handler import FileHandler
import os

# Initialize file handler with upload folder from config
file_handler = FileHandler(os.getenv('UPLOADS_FOLDER'))

@main.route('/products', methods=['GET'])
def get_products():

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    category_id = request.args.get('category_id', type=int)
    price_range = request.args.get('price_range', type=str)
    rating_range = request.args.get('rating_range', type=str)
    order_by = request.args.get('order_by', 'created_at', type=str)
    liked = request.args.get('liked', type=bool)
    
    query = Product.query.options(
        db.joinedload(Product.category),
        db.joinedload(Product.user)
    )
    
    # Apply filters if provided
    if liked:
        liked_products = current_user.liked_products.split(',')
        query = query.filter(Product.id.in_(liked_products))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if price_range:
        min_price, max_price = map(float, price_range.split(','))
        query = query.filter(Product.price >= min_price, Product.price <= max_price)
    if rating_range:
        min_rating, max_rating = map(float, rating_range.split(','))
        query = query.filter(Product.overall_rating >= min_rating, Product.overall_rating <= max_rating)
    
    # Sort products
    if order_by == 'price_descending':
        query = query.order_by(Product.price.desc())
    elif order_by == 'price_ascending':
        query = query.order_by(Product.price.asc())
    elif order_by == 'rating':
        query = query.order_by(Product.overall_rating.desc())
    elif order_by == 'created_at':
        query = query.order_by(Product.created_at.desc())
    else: 
        query = query.order_by(Product.created_at.desc())
    
    # Paginate
    products = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [{
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'price': p.price,
            'stock_quantity': p.stock_quantity,
            'images': p.images,
            'overall_rating': p.overall_rating,
            'category_id': p.category_id,
            'category_name': p.category.title,
            'seller_name': p.user.username
        } for p in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': products.page,
        'has_next': products.has_next,
        'has_prev': products.has_prev
    })

@main.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    
    return jsonify({
        'id': product.id,
        'title': product.title,
        'description': product.description,
        'price': product.price,
        'stock_quantity': product.stock_quantity,
        'images': product.images,
        'overall_rating': product.overall_rating,
        'category_id': product.category_id,
        'category_name': product.category.title,
        'seller_username': product.user.username
    })


@main.route('/products', methods=['POST'])
@login_required
def create_product():
    if not current_user.is_seller():
        abort(403, description="Only sellers can create products")
    
    try:
        # Handle form data
        data = request.form
        files = request.files.getlist('images')
        
        # Validate required fields
        required_fields = ['title', 'description', 'price', 'stock_quantity', 'category_id']
        for field in required_fields:
            if field not in data:
                abort(400, description=f"Missing required field: {field}")
        
        # Validate category
        if not Category.query.get(data['category_id']):
            abort(400, description="Invalid category")
        
        # Validate price and stock
        try:
            price = float(data['price'])
            stock = int(data['stock_quantity'])
            if price <= 0 or stock < 0:
                raise ValueError
        except ValueError:
            abort(400, description="Invalid price or stock quantity")
        
        # Save images
        image_paths = []
        for file in files:
            path = file_handler.save_file(file)
            if path:
                image_paths.append(path)
        
        if not image_paths and files:
            abort(400, description="Failed to upload images")
        
        # Create new product
        new_product = Product(
            title=data['title'],
            description=data.get('description', ''),
            images=image_paths,  # Store relative paths
            stock_quantity=stock,
            price=price,
            overall_rating=0.0,
            category_id=int(data['category_id']),
            user_id=current_user.id
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        # Convert relative paths to full URLs in response
        image_urls = [
            url_for('main.get_image', filename=path, _external=True)
            for path in image_paths
        ]
        
        return jsonify({
            'message': 'Product created successfully',
            'product': {
                'id': new_product.id,
                'title': new_product.title,
                'description': new_product.description,
                'price': new_product.price,
                'stock_quantity': new_product.stock_quantity,
                'images': image_urls,
                'category_id': new_product.category_id,
                'user_id': new_product.user_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Clean up uploaded files if product creation fails
        for path in image_paths:
            file_handler.delete_file(path)
        abort(500, description=str(e))

@main.route('/products/<int:id>', methods=['PUT'])
@login_required
def update_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        abort(403)
    files = request.files.getlist('images')

    # Get new images from file data
    image_paths = []
    for file in files:
        path = file_handler.save_file(file)
        if path:
            image_paths.append(path)
    
    if not image_paths and files:
        abort(400, description="Failed to upload images")

    data = request.get_json()
    
    # Maintain links to unchanged images
    unchanged_images = data.get('images', [])

    image_paths.extend(unchanged_images)
    product.images = image_paths

    product.title = data.get('title', product.title)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)
    product.stock_quantity = data.get('stock_quantity', product.stock_quantity)
    db.session.commit()
    return jsonify({'message': 'Product updated'})

@main.route('/products/<int:id>', methods=['DELETE'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        abort(403)
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})

# Add route to serve images
@main.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(os.getenv("UPLOADS_FOLDER"), filename)
