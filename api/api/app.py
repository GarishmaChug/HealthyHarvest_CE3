from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_restful import Api
from resources.resources import jwt, UserLoginResource, UserRegisterResource ,ProductResource , CartResource , UserResource
from models.models import db, User, Product, Cart

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
jwt.init_app(app)   
api = Api(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['JWT_SECRET_KEY'] = 'your-256-bit-secret-key-here-must-be-32-bytes-long'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


db.init_app(app)

# db = SQLAlchemy(app)
# class User(db.Model):
#     _tablename_ = 'user'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(150), unique=True, nullable=False)
#     email = db.Column(db.String(150), unique=True, nullable=False)
#     password = db.Column(db.String(256), nullable=False)
#     role = db.Column(db.String(50), nullable=False, default="user")
    
#     # Define relationship here (only once)
#     cart_items = db.relationship('Cart', backref='user', lazy=True)

# class Product(db.Model):
#     _tablename_ = 'product'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(150), nullable=False)
#     price = db.Column(db.Float, nullable=False)  # Changed to Float (store as number without $)
#     image = db.Column(db.String(150), nullable=True)
#     category = db.Column(db.String(50), nullable=False)
#     description = db.Column(db.Text, nullable=True)
    
#     # Relationship with Cart (only define once)
#     cart_items = db.relationship('Cart', backref='product', lazy=True)

# class Cart(db.Model):
#     _tablename_ = 'cart'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
#     quantity = db.Column(db.Integer, default=1)
#     price = db.Column(db.Float, nullable=False)  # Should match Product.price type
    
    # No need to redefine the relationship here since it's defined in Product
    # The backref='product' in Product model creates this automatically




# --- API ENDPOINTS ---
@app.route('/api/products', methods=['GET'])
def api_get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'image': p.image,
        'category': p.category,
        'description': p.description
    } for p in products])

@app.route('/api/products/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'category': product.category,
        'description': product.description
    })

@app.route('/api/products', methods=['POST'])
def api_create_product():
    data = request.get_json()
    new_product = Product(
        name=data['name'],
        price=data['price'],
        image=data.get('image'),
        category=data['category'],
        description=data.get('description', '')
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product created', 'id': new_product.id}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def api_update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.price = data.get('price', product.price)
    product.image = data.get('image', product.image)
    product.category = data.get('category', product.category)
    product.description = data.get('description', product.description)
    db.session.commit()
    return jsonify({'message': 'Product updated'})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def api_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})

# --- END OF API ENDPOINTS ---

# --- API ENDPOINTS ---

@app.route('/api/cart', methods=['GET'])
def get_all_carts():
    carts = Cart.query.all()
    return jsonify([{
        'id': item.id,
        'user_id': item.user_id,
        'product_id': item.product_id,
        'quantity': item.quantity,
        'price': item.price
    } for item in carts])


@app.route('/api/cart/<int:user_id>', methods=['GET'])
def api_get_cart(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': item.id,
        'product_id': item.product_id,
        'product_name': item.product.name,
        'quantity': item.quantity,
        'price': item.price
    } for item in cart_items])

@app.route('/api/cart', methods=['POST'])
def api_add_to_cart():
    data = request.get_json()
    user_id = data['user_id']
    product_id = data['product_id']
    quantity = data.get('quantity', 1)

    product = Product.query.get_or_404(product_id)

    # Check if already in cart
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            price=product.price
        )
        db.session.add(cart_item)

    db.session.commit()
    return jsonify({'message': 'Item added to cart', 'item_id': cart_item.id}), 201

@app.route('/api/cart/<int:item_id>', methods=['PUT'])
def api_update_cart_item(item_id):
    data = request.get_json()
    cart_item = Cart.query.get_or_404(item_id)
    quantity = data.get('quantity')

    if quantity is not None and quantity > 0:
        cart_item.quantity = quantity

    if 'price' in data and data['price'] > 0:
        cart_item.price = data['price']    
        db.session.commit()
        return jsonify({'message': 'Cart updated'})
    else:
        return jsonify({'error': 'Invalid quantity'}), 400

@app.route('/api/cart/<int:item_id>', methods=['DELETE'])
def api_delete_cart_item(item_id):
    try:
        # Get the cart item to be deleted
        cart_item = Cart.query.get_or_404(item_id)
        
        # Get all cart items with the same product_id for this user
        user_cart_items = Cart.query.filter_by(
            user_id=cart_item.user_id,
            product_id=cart_item.product_id
        ).all()
        
        # Delete all matching items
        for item in user_cart_items:
            db.session.delete(item)
        
        db.session.commit()
        return jsonify({'message': 'All instances of this product have been removed from your cart'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# --- END OF API ENDPOINTS ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def cleanup_duplicate_cart_items():
    try:
        # Get all cart items
        all_cart_items = Cart.query.all()
        
        # Dictionary to track processed items
        processed = {}
        
        # List to store items to delete
        items_to_delete = []
        
        for item in all_cart_items:
            key = (item.user_id, item.product_id)
            
            if key in processed:
                # If we've seen this user_id and product_id combination before,
                # add this item to the deletion list
                items_to_delete.append(item)
            else:
                # First time seeing this combination, mark as processed
                processed[key] = item
        
        # Delete duplicate items
        for item in items_to_delete:
            db.session.delete(item)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error cleaning up cart items: {str(e)}")
        return False

def initialize_database():
    with app.app_context():
        db.create_all()
        cleanup_duplicate_cart_items()  # Clean up any existing duplicates
        
        # Create test admin user if not exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created test admin user")
        
        # Create test regular user if not exists
        user = User.query.filter_by(email='user@example.com').first()
        if not user:
            user = User(
                username='user',
                email='user@example.com',
                role='user'
            )
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            print("Created test regular user")
        
        beauty_products = []
        pharmacy_products = []
        fruits_products = []
        snacks_products = []
        other_products = []
        # Create admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin = User(
                username='admin',
                email='admin@example.com',
                password=hashed_password,
                role='admin'
            )
            db.session.add(admin)
          
            db.session.commit()
        
        if Product.query.count() == 0:
            beauty_products = [
    {'name': 'Sol de Janeiro Beija Flor Jet Set', 'price': 32.0, 'image': 'static/images/product1.webp', 'category': 'beauty'},
    {'name': 'Charlotte Tilbury Beauty Pillow Talk Mini', 'price': 25.0, 'image': 'static/images/product2.webp', 'category': 'beauty'},
    {'name': 'Sol de Janeiro Bom Dia Bright Jet set', 'price': 33.0, 'image': 'static/images/product3.jpg', 'category': 'beauty'},
    {'name': 'Glow Recipe Fruit Babies Bestsellers Kit', 'price': 250.0, 'image': 'static/images/product4.jpeg', 'category': 'beauty'},
    {'name': 'Fenty Beauty Pro Filtr Foundation', 'price': 38.0, 'image': 'static/images/product5.jpeg', 'category': 'beauty'},
    {'name': 'Urban Decay Naked3 Eyeshadow Palette', 'price': 54.0, 'image': 'static/images/product6.jpeg', 'category': 'beauty'},
    {'name': 'Anastasia Beverly Hills Brow Wiz', 'price': 21.0, 'image': 'static/images/product7.jpeg', 'category': 'beauty'},
    {'name': 'Too Faced Better Than Sex Mascara', 'price': 25.0, 'image': 'static/images/product8.jpeg', 'category': 'beauty'},
    {'name': 'MAC Cosmetics Matte Lipstick', 'price': 19.0, 'image': 'static/images/product9.jpeg', 'category': 'beauty'},
    {'name': 'Tarte Shape Tape Concealer', 'price': 27.0, 'image': 'static/images/product10.jpeg', 'category': 'beauty'},
    {'name': 'Maybelline Fit Me Foundation', 'price': 10.0, 'image': 'static/images/product11.jpeg', 'category': 'beauty'},
    {'name': 'Huda Beauty Desert Dusk Palette', 'price': 65.0, 'image': 'static/images/product12.jpeg', 'category': 'beauty'},
    {'name': 'NARS Radiant Creamy Concealer', 'price': 30.0, 'image': 'static/images/product13.jpeg', 'category': 'beauty'},
    {'name': 'Fenty Beauty Killawatt Highlighter', 'price': 36.0, 'image': 'static/images/product14.jpeg', 'category': 'beauty'},
    {'name': 'L`Oréal Lash Paradise Mascara', 'price': 12.0, 'image': 'static/images/product15.jpeg', 'category': 'beauty'},
    {'name': 'Benefit Cosmetics Hoola Bronzer', 'price': 30.0, 'image': 'static/images/product16.jpeg', 'category': 'beauty'},
    {'name': 'Charlotte Tilbury Airbrush Powder', 'price': 45.0, 'image': 'static/images/product17.jpeg', 'category': 'beauty'},
    {'name': 'Becca Shimmering Skin Perfector', 'price': 38.0, 'image': 'static/images/product18.jpeg', 'category': 'beauty'},
    {'name': 'IT Cosmetics CC+ Cream', 'price': 39.0, 'image': 'static/images/product19.jpeg', 'category': 'beauty'},
    {'name': 'Tatcha The Dewy Skin Cream', 'price': 68.0, 'image': 'static/images/product20.jpeg', 'category': 'beauty'}
]

            # Pharmacy Products (20 items)
            pharmacy_products = [
        
    {"name": "Pain Reliever Tablet", "price": 12.99, "image": "static/images/painrelif.jpg", "category": "pharmacy"},
    {"name": "Cough Syrup", "price": 8.50, "image": "static/images/cough.jpg", "category": "pharmacy"},
    {"name": "Multivitamin Capsules", "price": 15.75, "image": "static/images/multivitamin.jpg", "category": "pharmacy"},
    {"name": "Antibiotic Ointment", "price": 5.99, "image": "static/images/onitment.jpg", "category": "pharmacy"},
    {"name": "Cold Relief Capsules", "price": 10.30, "image": "static/images/cold.jpg", "category": "pharmacy"},
    {"name": "Allergy Relief Tablets", "price": 7.99, "image": "static/images/allergy.jpg", "category": "pharmacy"},
    {"name": "Digestive Aid Tablets", "price": 6.50, "image": "static/images/digestive.jpg", "category": "pharmacy"},
    {"name": "Vitamin D3 Supplement", "price": 9.00, "image": "static/images/vitaminD3.jpg", "category": "pharmacy"},
    {"name": "Antacid Tablets", "price": 3.75, "image": "static/images/amtacid.jpg", "category": "pharmacy"},
    {"name": "Headache Relief Gel", "price": 4.99, "image": "static/images/haedache.jpg", "category": "pharmacy"},
    {"name": "Hair Growth Shampoo", "price": 12.00, "image": "static/images/hair.jpg", "category": "pharmacy"},
    {"name": "Sleep Aid Tablets", "price": 8.40, "image": "static/images/sleep.jpg", "category": "pharmacy"},
    {"name": "Band-Aids", "price": 2.99, "image": "static/images/bandaid.jpg", "category": "pharmacy"},
    {"name": "Eye Drops", "price": 5.50, "image": "static/images/eyedrops.jpg", "category": "pharmacy"},
    {"name": "Muscle Relief Cream", "price": 7.25, "image": "static/images/muscle.jpg", "category": "pharmacy"},
    {"name": "Moisturizing Lotion", "price": 6.80, "image": "static/images/moisturizing.jpg", "category": "pharmacy"},
    {"name": "Thermometer", "price": 15.99, "image": "static/images/thermometer.jpeg", "category": "pharmacy"},
    {"name": "Sunscreen Lotion", "price": 12.99, "image": "static/images/sunscreen.jpg", "category": "pharmacy"},
    {"name": "First Aid Kit", "price": 25.00, "image": "static/images/firstaid.jpg", "category": "pharmacy"},
    {"name": "Cold Compress", "price": 8.50, "image": "static/images/compress.jpg", "category": "pharmacy"}
]

            

        # Fruits & Vegetables (30 items)
            fruits_products = [
          

    {'name': 'Apple', 'price': 1.56, 'image': 'static/images/apple.png', 'category': 'fruits'},
    {'name': 'Banana', 'price': 0.53, 'image': 'static/images/banana.png', 'category': 'fruits'},
    {'name': 'Mango', 'price': 1.20, 'image': 'static/images/mango.png', 'category': 'fruits'},
    {'name': 'Orange', 'price': 0.78, 'image': 'static/images/orange.png', 'category': 'fruits'},
    {'name': 'Litchi', 'price': 1.20, 'image': 'static/images/litchi.png', 'category': 'fruits'},
    {'name': 'Kiwi', 'price': 1.48, 'image': 'static/images/kiwi.png', 'category': 'fruits'},
    {'name': 'Dragon Fruit', 'price': 0.76, 'image': 'static/images/dragonfruit.png', 'category': 'fruits'},
    {'name': 'Pineapple', 'price': 1.12, 'image': 'static/images/pineapple.png', 'category': 'fruits'},
    {'name': 'Strawberry', 'price': 1.15, 'image': 'static/images/strawberry.png', 'category': 'fruits'},
    {'name': 'Grapes', 'price': 0.84, 'image': 'static/images/grapes.png', 'category': 'fruits'},
    {'name': 'Carrot', 'price': 0.24, 'image': 'static/images/carrot.png', 'category': 'fruits'},
    {'name': 'Pomegranate', 'price': 1.38, 'image': 'static/images/pomegranet.png', 'category': 'fruits'},
    {'name': 'Watermelon', 'price': 0.42, 'image': 'static/images/watermelon.png', 'category': 'fruits'},
    {'name': 'Muskmelon', 'price': 0.80, 'image': 'static/images/muskmelon.png', 'category': 'fruits'},
    {'name': 'Papaya', 'price': 1.33, 'image': 'static/images/papaya.png', 'category': 'fruits'},
    {'name': 'Guava', 'price': 1.44, 'image': 'static/images/guava.png', 'category': 'fruits'},
    {'name': 'Potato', 'price': 0.36, 'image': 'static/images/potato.png', 'category': 'fruits'},
    {'name': 'Tomato', 'price': 0.48, 'image': 'static/images/tomato.png', 'category': 'fruits'},
    {'name': 'Green Chilli', 'price': 0.17, 'image': 'static/images/greenChilli.png', 'category': 'fruits'},
    {'name': 'Cauliflower', 'price': 0.18, 'image': 'static/images/cauliflower.png', 'category': 'fruits'},
    {'name': 'Ginger', 'price': 0.28, 'image': 'static/images/ginger.png', 'category': 'fruits'},
    {'name': 'Capsicum', 'price': 0.96, 'image': 'static/images/capsicum.png', 'category': 'fruits'},
    {'name': 'Mushroom', 'price': 0.60, 'image': 'static/images/mushroom.png', 'category': 'fruits'},
    {'name': 'Garlic', 'price': 1.02, 'image': 'static/images/garlic.png', 'category': 'fruits'},
    {'name': 'Cucumber', 'price': 0.36, 'image': 'static/images/cucumber.png', 'category': 'fruits'},
    {'name': 'Beans', 'price': 0.35, 'image': 'static/images/beans.png', 'category': 'fruits'},
    {'name': 'Radish', 'price': 0.36, 'image': 'static/images/raddish.png', 'category': 'fruits'},
    {'name': 'Lemon', 'price': 0.36, 'image': 'static/images/lemon.png', 'category': 'fruits'},
    {'name': 'Broccoli', 'price': 0.30, 'image': 'static/images/broccoli.png', 'category': 'fruits'},
    {'name': 'Onion', 'price': 0.60, 'image': 'static/images/onion.png', 'category': 'fruits'}
]



            

            # Snacks (30 items)
        snacks_products = [
         
 
    {'name': 'Maggi Noodles', 'price': 0.12, 'image': 'static/images/maggi.png', 'category': 'snacks'},
    {'name': 'Tedhe Medhe', 'price': 0.12, 'image': 'static/images/tedhemedhe.png', 'category': 'snacks'},
    {'name': "Lay's Magic Masala", 'price': 0.12, 'image': 'static/images/Bluelays.png', 'category': 'snacks'},
    {'name': "Lay's Classic Salted", 'price': 0.12, 'image': 'static/images/Yellowlays.png', 'category': 'snacks'},
    {'name': "Lay's Cream & Onion", 'price': 0.12, 'image': 'static/images/GreenLays.png', 'category': 'snacks'},
    {'name': "Maggi Cheese Pasta", 'price': 0.42, 'image': 'static/images/cheese.png', 'category': 'snacks'},
    {'name': "Maggi Masala Pasta", 'price': 0.42, 'image': 'static/images/masala.png', 'category': 'snacks'},
    {'name': "Oreo Cookies", 'price': 0.12, 'image': 'static/images/oreo.png', 'category': 'snacks'},
    {'name': "Dark Fantasy", 'price': 0.36, 'image': 'static/images/darkfantasy.png', 'category': 'snacks'},
    {'name': "Hide & Seek", 'price': 0.36, 'image': 'static/images/hide.png', 'category': 'snacks'},
    {'name': "Jim Jam", 'price': 0.12, 'image': 'static/images/jimjam.png', 'category': 'snacks'},
    {'name': "Good Day", 'price': 0.12, 'image': 'static/images/gooday.png', 'category': 'snacks'},
    {'name': "Little Hearts", 'price': 0.12, 'image': 'static/images/hearts.png', 'category': 'snacks'},
    {'name': "Ferrero Rocher", 'price': 9.16, 'image': 'static/images/ferrero.png', 'category': 'snacks'},
    {'name': "Dairy Milk Silk", 'price': 2.23, 'image': 'static/images/fruitNut.png', 'category': 'snacks'},
    {'name': "Kit Kat", 'price': 1.32, 'image': 'static/images/kitkat.png', 'category': 'snacks'},
    {'name': "Crispello", 'price': 0.48, 'image': 'static/images/crispello.png', 'category': 'snacks'},
    {'name': "Munch", 'price': 0.68, 'image': 'static/images/munch.png', 'category': 'snacks'},
    {'name': "Thums Up", 'price': 0.48, 'image': 'static/images/thumsup.png', 'category': 'snacks'},
    {'name': "Choco Latte", 'price': 1.44, 'image': 'static/images/chocolatte.png', 'category': 'snacks'},
    {'name': "Cold Coffee", 'price': 1.44, 'image': 'static/images/coldcoffee.png', 'category': 'snacks'},
    {'name': "Diet Coke", 'price': 0.48, 'image': 'static/images/diet.png', 'category': 'snacks'},
    {'name': "Fanta", 'price': 0.48, 'image': 'static/images/fanta.png', 'category': 'snacks'},
    {'name': "Sprite", 'price': 0.48, 'image': 'static/images/sprite.png', 'category': 'snacks'},
    {'name': "Limca", 'price': 0.48, 'image': 'static/images/limca.png', 'category': 'snacks'},
    {'name': "Maza", 'price': 0.48, 'image': 'static/images/maza.png', 'category': 'snacks'},
    {'name': "Mountain Dew", 'price': 1.03, 'image': 'static/images/dew.png', 'category': 'snacks'},
    {'name': "Aloo Bhujia", 'price': 2.65, 'image': 'static/images/bhujia.png', 'category': 'snacks'},
    {'name': "Kinder Joy", 'price': 0.58, 'image': 'static/images/joy.png', 'category': 'snacks'},
    {'name': "Makhana", 'price': 1.92, 'image': 'static/images/makhana.png', 'category': 'snacks'}
]




            # Other Grocery Items (33 items)
        other_products = [
        

    {'name': "Amul Moti Milk", 'price': 0.40, 'image': 'static/images/milk.png', 'category': 'other'},
    {'name': "Whole Wheat Bread", 'price': 0.72, 'image': 'static/images/wheatbread.png', 'category': 'other'},
    {'name': "Brown Bread", 'price': 0.66, 'image': 'static/images/brownbread.png', 'category': 'other'},
    {'name': "Pav Bread", 'price': 0.54, 'image': 'static/images/pavbread.png', 'category': 'other'},
    {'name': "Eggs", 'price': 0.86, 'image': 'static/images/eggs.png', 'category': 'other'},
    {'name': "Corn Flakes", 'price': 1.44, 'image': 'static/images/cornflakes.png', 'category': 'other'},
    {'name': "Muesli", 'price': 6.53, 'image': 'static/images/muesli.png', 'category': 'other'},
    {'name': "Oats", 'price': 0.82, 'image': 'static/images/oats.png', 'category': 'other'},
    {'name': "Curd", 'price': 0.30, 'image': 'static/images/curd.png', 'category': 'other'},
    {'name': "Salted Butter", 'price': 0.72, 'image': 'static/images/butter.png', 'category': 'other'},
    {'name': "Cheese Slices", 'price': 1.02, 'image': 'static/images/cheese.png', 'category': 'other'},
    {'name': "Fresh Cream", 'price': 0.82, 'image': 'static/images/cream.png', 'category': 'other'},
    {'name': "Condensed Milk", 'price': 1.68, 'image': 'static/images/condensedmilk.png', 'category': 'other'},
    {'name': "Peanut Butter", 'price': 1.75, 'image': 'static/images/peanutbutter.png', 'category': 'other'},
    {'name': "Honey", 'price': 1.38, 'image': 'static/images/honey.png', 'category': 'other'},
    {'name': "Tomato Ketchup", 'price': 1.20, 'image': 'static/images/ketchup.png', 'category': 'other'},
    {'name': "Mayonnaise", 'price': 0.59, 'image': 'static/images/mayo.png', 'category': 'other'},
    {'name': "Schezwan Chutney", 'price': 1.01, 'image': 'static/images/chutney.png', 'category': 'other'},
    {'name': "Chocolate Syrup", 'price': 1.26, 'image': 'static/images/chocolatesyrup.png', 'category': 'other'},
    {'name': "Ginger Garlic Paste", 'price': 0.55, 'image': 'static/images/gingergarlic.png', 'category': 'other'},
    {'name': "Vinegar", 'price': 0.80, 'image': 'static/images/vinegar.png', 'category': 'other'},
    {'name': "Premium Tea", 'price': 1.68, 'image': 'static/images/tea.png', 'category': 'other'},
    {'name': "Taj Mahal Tea", 'price': 0.78, 'image': 'static/images/tajtea.png', 'category': 'other'},
    {'name': "Instant Coffee", 'price': 2.76, 'image': 'static/images/coffee.png', 'category': 'other'},
    {'name': "Whole Wheat Flour", 'price': 2.86, 'image': 'static/images/wheatflour.png', 'category': 'other'},
    {'name': "Basmati Rice", 'price': 4.98, 'image': 'static/images/rice.png', 'category': 'other'},
    {'name': "Kabuli Chana", 'price': 1.87, 'image': 'static/images/chana.png', 'category': 'other'},
    {'name': "Red Rajma", 'price': 1.44, 'image': 'static/images/rajma.png', 'category': 'other'},
    {'name': "Toor Dal", 'price': 2.38, 'image': 'static/images/toordal.png', 'category': 'other'},
    {'name': "Urad Dal", 'price': 0.92, 'image': 'static/images/uraddal.png', 'category': 'other'},
    {'name': "Brown Chana", 'price': 0.79, 'image': 'static/images/brownchana.png', 'category': 'other'},
    {'name': "Chewing Gum", 'price': 0.59, 'image': 'static/images/gum.png', 'category': 'other'},
    {'name': "Choco Pie", 'price': 0.96, 'image': 'static/images/chocopie.png', 'category': 'other'}
]



            

        all_products = beauty_products + pharmacy_products + fruits_products + snacks_products + other_products
            
        for product in all_products:
            if not Product.query.filter_by(name=product['name']).first():
                    new_product = Product(
                        name=product['name'],
                        price=product['price'],
                        image=product['image'],
                        category=product['category']
                    )
                    db.session.add(new_product)
            
 
        db.session.commit()
        print("Database initialized with all products and admin user.")

# Admin routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    products = Product.query.all()
    return render_template('admin_dashboard.html', products=products)

@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        description = request.form.get('description', '')
        

        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = os.path.join('uploads', filename)
        
        new_product = Product(
            name=name,
            price=price,
            image=image,
            category=category,
            description=description
        )
        
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_product.html')

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = request.form['price']
        product.category = request.form['category']
        product.description = request.form.get('description', '')
        
        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image = os.path.join('uploads', filename)
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_product.html', product=product)

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    
 
    Cart.query.filter_by(product_id=product_id).delete()
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/beauty')
def beauty():
    products = Product.query.filter_by(category='beauty').all()
    return render_template('beauty.html', products=products)

@app.route('/pharmacy')
def pharmacy():
    products = Product.query.filter_by(category='pharmacy').all()
    return render_template('pharmacy.html', products=products)

@app.route('/fruits&veg')
def fruits():
    products = Product.query.filter_by(category='fruits').all()
    return render_template('fruits&veg.html', products=products)

@app.route('/snacks')
def snacks():
    products = Product.query.filter_by(category='snacks').all()
    return render_template('snacks.html', products=products)

@app.route('/all')
def all_products():
    products = Product.query.filter_by(category='other').all()
    return render_template('all.html', products=products)
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('Please log in to add items to your cart.', 'warning')
        return redirect(url_for('login'))

    product = Product.query.get_or_404(product_id)
    quantity = request.form.get('quantity', type=int, default=1)
    
    cart_item = Cart.query.filter_by(
        user_id=session['user_id'],
        product_id=product_id
    ).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        new_item = Cart(
            user_id=session['user_id'],
            product_id=product_id,
            quantity=quantity,
            price=product.price
        )
        db.session.add(new_item)
    
    db.session.commit()
    flash(f'{quantity} {product.name}(s) added to cart!', 'success')
    return redirect(request.referrer or url_for('home'))
@app.route('/cart')
def view_cart():
    if 'user_id' not in session:
        flash('Please log in to view your cart.', 'warning')
        return redirect(url_for('login'))

    cart_items = Cart.query.filter_by(user_id=session['user_id']).all()
    total = sum(item.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cart/update/<int:item_id>', methods=['GET', 'POST'])
def update_cart_quantity(item_id):
    if request.method == 'POST':
        # Try to get user from JWT first
        try:
            user_id = get_jwt_identity()
        except:
            # Fall back to session if JWT fails
            if 'user_id' not in session:
                flash('Please log in to update cart', 'error')
                return redirect(url_for('login'))
            user_id = session['user_id']

        quantity = request.form.get('quantity', type=int)
        if not quantity or quantity < 1:
            flash('Invalid quantity', 'error')
            return redirect(url_for('view_cart'))
        
        cart_item = Cart.query.get_or_404(item_id)
        if cart_item.user_id != user_id:
            flash('Unauthorized', 'error')
            return redirect(url_for('view_cart'))
        
        cart_item.quantity = quantity
        db.session.commit()
        flash('Cart updated successfully', 'success')
        return redirect(url_for('view_cart'))
    else:
        return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:item_id>', methods=['GET', 'POST'])
def remove_from_cart(item_id):
    if request.method == 'POST':
        # Try to get user from JWT first
        try:
            user_id = get_jwt_identity()
        except:
            # Fall back to session if JWT fails
            if 'user_id' not in session:
                flash('Please log in to manage your cart.', 'warning')
                return redirect(url_for('login'))
            user_id = session['user_id']

        cart_item = Cart.query.get_or_404(item_id)
        if cart_item.user_id != user_id:
            flash('You cannot remove this item.', 'danger')
            return redirect(url_for('view_cart'))

        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'success')
        return redirect(url_for('view_cart'))
    else:
        return redirect(url_for('view_cart'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash('Email or username already registered!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Check if it's an API request (JSON)
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            # Regular form submission
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'user')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            # Create JWT token
            access_token = create_access_token(identity=user.id)
            
            if request.is_json:
                return jsonify({
                    'access_token': access_token,
                    'user_id': user.id,
                    'username': user.username,
                    'role': user.role
                })
            else:
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404
@app.route('/privacy_policy')
def policy():
    return render_template('privacy.html')
@app.route('/faq')
def faq():
    return render_template('faq.html')
@app.route('/terms')
def terms():
    return render_template('terms.html')
@app.errorhandler(500)
def internal_error(error):
    return "An internal error occurred", 500
@app.route('/search')
def search():
    query = request.args.get('query', '').strip().lower()
    
    if query:
        # Database query with search across multiple fields
        results = Product.query.filter(
            or_(
                Product.name.ilike(f'%{query}%'),     # Case-insensitive LIKE
                Product.category.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%')
            )
        ).all()
    else:
        # Return all products if no search query
        results = Product.query.all()
    
    return render_template('search_results.html',
                         query=query,
                         results=results)

@app.route('/checkout', methods=['POST','GET'])
def checkout():
    if 'user_id' not in session:
        flash('Please log in to checkout.', 'warning')
        return redirect(url_for('login'))

    Cart.query.filter_by(user_id=session['user_id']).delete()
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return render_template('checkout.html')
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session['username'], role=session['role'])

# Add resources to API
api.add_resource(UserRegisterResource, '/api/register')
api.add_resource(UserLoginResource, '/api/login')
api.add_resource(ProductResource, '/api/products', '/api/products/<int:product_id>')
# api.add_resource(CartResource, '/api/cart', '/api/cart/<int:item_id>')
api.add_resource(UserResource, '/api/users', '/api/users/<int:user_id>')


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(debug=True, port=3000)