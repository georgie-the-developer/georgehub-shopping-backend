from flask import jsonify, request, abort
from flask_login import login_required, current_user
from ..models import db, Review
from . import review_bp as main

@main.route('/products/<int:product_id>/reviews', methods=['GET'])
def get_reviews(product_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    
    reviews = Review.query.options(
        db.joinedload(Review.user)
    ).filter_by(product_id=product_id)\
    .order_by(Review.created_at.desc())\
    .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [{
            'id': r.id,
            'body': r.body,
            'rating': r.rating,
            'created_at': r.created_at,
            'user_id': r.user_id,
            'username': r.user.username,
            'product_id': r.product_id
        } for r in reviews.items],
        'total': reviews.total,
        'pages': reviews.pages,
        'current_page': reviews.page,
        'has_next': reviews.has_next,
        'has_prev': reviews.has_prev
    })

@main.route('/products/<int:product_id>/reviews', methods=['POST'])
@login_required
def create_review(product_id):
    if not current_user.is_buyer():
        abort(403)
    
    data = request.get_json()
    review = Review(
        body=data.get('body'),
        rating=data['rating'],
        product_id=product_id,
        user_id=current_user.id
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({'message': 'Review created', 'id': review.id}), 201

@main.route('/reviews/<int:id>', methods=['DELETE'])
@login_required
def delete_review(id):
    review = Review.query.get_or_404(id)
    if review.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    
    db.session.delete(review)
    db.session.commit()
    return jsonify({'message': 'Review deleted'})