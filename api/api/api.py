from flask import Blueprint, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Product, Cart
from werkzeug.utils import secure_filename
import os

# Initialize JWT
jwt = JWTManager(app)

# Create Blueprint for API
api = Blueprint('api', __name__)

# Helper function for file upload
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# User CRUD Operations
@api.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    } for user in users]), 200

@api.route('/api/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    }), 200

@api.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        user.password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    if 'role' in data and current_user.role == 'admin':
        user.role = data['role']
    
    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200

@api.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

# Product CRUD Operations
@api.route('/api/products', methods=['POST'])
@jwt_required()
def create_product():
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.form
    if not all(k in data for k in ('name', 'price', 'category')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    image = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image = os.path.join('uploads', filename)
    
    new_product = Product(
        name=data['name'],
        price=float(data['price']),
        category=data['category'],
        description=data.get('description', ''),
        image=image
    )
    
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product created successfully', 'id': new_product.id}), 201

@api.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    product = Product.query.get_or_404(product_id)
    data = request.form
    
    if 'name' in data:
        product.name = data['name']
    if 'price' in data:
        product.price = float(data['price'])
    if 'category' in data:
        product.category = data['category']
    if 'description' in data:
        product.description = data['description']
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            product.image = os.path.join('uploads', filename)
    
    db.session.commit()
    return jsonify({'message': 'Product updated successfully'}), 200

@api.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    product = Product.query.get_or_404(product_id)
    
    # Delete associated cart items
    Cart.query.filter_by(product_id=product_id).delete()
    
    # Delete product image if exists
    if product.image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.image))
        except:
            pass
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'}), 200

# Cart CRUD Operations
@api.route('/api/cart', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    
    return jsonify([{
        'id': item.id,
        'product_id': item.product_id,
        'quantity': item.quantity,
        'price': item.price,
        'product_name': item.product.name,
        'product_image': item.product.image
    } for item in cart_items]), 200

@api.route('/api/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'product_id' not in data:
        return jsonify({'error': 'Product ID is required'}), 400
    
    product = Product.query.get_or_404(data['product_id'])
    quantity = data.get('quantity', 1)  # Default to 1 if quantity not specified
    
    cart_item = Cart.query.filter_by(
        user_id=user_id,
        product_id=data['product_id']
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(
            user_id=user_id,
            product_id=data['product_id'],
            quantity=quantity,
            price=product.price
        )
        db.session.add(cart_item)
    
    db.session.commit()
    return jsonify({
        'message': 'Item added to cart',
        'quantity': quantity,
        'product_name': product.name
    }), 201

@api.route('/api/cart/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_cart_quantity(item_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'quantity' not in data:
        return jsonify({'error': 'Quantity is required'}), 400
    
    cart_item = Cart.query.get_or_404(item_id)
    
    if cart_item.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    cart_item.quantity = data['quantity']
    db.session.commit()
    return jsonify({'message': 'Cart updated successfully'}), 200

@api.route('/api/cart/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    user_id = get_jwt_identity()
    cart_item = Cart.query.get_or_404(item_id)
    
    if cart_item.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Item removed from cart'}), 200

# Register the blueprint
app.register_blueprint(api) 