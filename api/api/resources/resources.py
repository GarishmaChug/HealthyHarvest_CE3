from flask import request
from flask_restful import Resource
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models.models import db, User, Product, Cart

jwt = JWTManager()

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    try:
        identity = jwt_data["sub"]
        return User.query.get(identity)
    except Exception as e:
        print(f"Error in user lookup: {str(e)}")
        return None

class UserRegisterResource(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if User.query.filter_by(email=email).first():
            return {"message": "Email already exists."}, 400
            
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        return {"message": "User registered successfully."}, 201

class UserLoginResource(Resource):
    def post(self):
        data = request.get_json()

        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            # Create token with additional claims
            access_token = create_access_token(
                identity=user.id,
                additional_claims={
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role
                }
            )
            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "user_id": user.id,
                "username": user.username,
                "role": user.role
            }, 200

        return {"message": "Invalid credentials."}, 401

class ProductResource(Resource):
    def get(self, product_id=None):
        if product_id:
            product = Product.query.get_or_404(product_id)
            return {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "category": product.category,
                "description": product.description,
                "image": product.image
            }
        
        category = request.args.get("category")
        if category:
            products = Product.query.filter_by(category=category).all()
        else:
            products = Product.query.all()
        
        return [{
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "category": p.category,
            "description": p.description,
            "image": p.image
        } for p in products]

    @jwt_required()
    def post(self):
        data = request.get_json()
        
        new_product = Product(
            name=data.get("name"),
            price=data.get("price"),
            category=data.get("category"),
            description=data.get("description"),
            image=data.get("image")
        )
        
        db.session.add(new_product)
        db.session.commit()
        return {"message": "Product created successfully", "id": new_product.id}, 201

    @jwt_required()
    def put(self, product_id):
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if data.get("name"):
            product.name = data.get("name")
        if data.get("price"):
            product.price = data.get("price")
        if data.get("category"):
            product.category = data.get("category")
        if data.get("description"):
            product.description = data.get("description")
        if data.get("image"):
            product.image = data.get("image")
        
        db.session.commit()
        return {"message": "Product updated successfully"}

    @jwt_required()
    def delete(self, product_id):
        product = Product.query.get_or_404(product_id)
        Cart.query.filter_by(product_id=product_id).delete()
        db.session.delete(product)
        db.session.commit()
        return {"message": "Product deleted successfully"}

class CartResource(Resource):
    @jwt_required()
    def get(self, item_id=None):
        user_id = get_jwt_identity()
        
        if item_id:
            # Get specific cart item
            cart_item = Cart.query.get_or_404(item_id)
            if cart_item.user_id != user_id:
                return {"message": "Unauthorized"}, 403
                
            return {
                "id": cart_item.id,
                "product_id": cart_item.product_id,
                "quantity": cart_item.quantity,
                "price": cart_item.price,
                "product_name": cart_item.product.name,
                "product_image": cart_item.product.image
            }
        else:
            # Get all cart items for user
            cart_items = Cart.query.filter_by(user_id=user_id).all()
            return [{
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "product_name": item.product.name,
                "product_image": item.product.image
            } for item in cart_items]

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json()
        
        product_id = data.get("product_id")
        quantity = data.get("quantity", 1)
        
        if not product_id:
            return {"message": "Product ID is required"}, 400
        
        product = Product.query.get_or_404(product_id)
        
        # Check if item already in cart
        cart_item = Cart.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()
        
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
        return {"message": "Item added to cart", "item_id": cart_item.id}, 201

    @jwt_required()
    def put(self, item_id):
        user_id = get_jwt_identity()
        cart_item = Cart.query.get_or_404(item_id)
        
        if cart_item.user_id != user_id:
            return {"message": "Unauthorized"}, 403
        
        data = request.get_json()
        quantity = data.get("quantity")
        
        if not quantity or quantity < 1:
            return {"message": "Valid quantity is required"}, 400
            
        cart_item.quantity = quantity
        db.session.commit()
        return {"message": "Cart updated successfully"}

    @jwt_required()
    def delete(self, item_id):
        user_id = get_jwt_identity()
        cart_item = Cart.query.get_or_404(item_id)
        
        if cart_item.user_id != user_id:
            return {"message": "Unauthorized"}, 403
        
        # Delete all instances of this product for this user
        Cart.query.filter_by(
            user_id=user_id,
            product_id=cart_item.product_id
        ).delete()
        
        db.session.commit()
        return {"message": "All instances of this product have been removed from your cart"}

class UserResource(Resource):
    @jwt_required()
    def get(self, user_id=None):
        try:
            print("Getting user data...")
            current_user_id = get_jwt_identity()
            print(f"Current user ID: {current_user_id}")
            
            current_user = User.query.get(current_user_id)
            print(f"Current user role: {current_user.role}")
            
            if user_id:
                print(f"Getting specific user: {user_id}")
                user = User.query.get_or_404(user_id)
                if current_user.role != 'admin' and current_user.id != user_id:
                    return {"message": "Unauthorized access"}, 403
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            
            # Get all users (admin only)
            if current_user.role != 'admin':
                return {"message": "Unauthorized access"}, 403
                
            users = User.query.all()
            print(f"Found {len(users)} users")
            return [{
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            } for user in users]
        except Exception as e:
            print(f"Error in get: {str(e)}")
            return {"message": "Error occurred", "error": str(e)}, 500

    @jwt_required()
    def put(self, user_id):
        # Only allow users to update their own profile or admin to update any profile
        current_user = User.query.get(get_jwt_identity())
        if current_user.id != user_id and current_user.role != 'admin':
            return {"message": "Unauthorized access"}, 403

        user = User.query.get_or_404(user_id)
        data = request.get_json()

        if data.get("username"):
            # Check if username is already taken
            existing_user = User.query.filter_by(username=data["username"]).first()
            if existing_user and existing_user.id != user_id:
                return {"message": "Username already exists"}, 400
            user.username = data["username"]

        if data.get("email"):
            # Check if email is already taken
            existing_user = User.query.filter_by(email=data["email"]).first()
            if existing_user and existing_user.id != user_id:
                return {"message": "Email already exists"}, 400
            user.email = data["email"]

        if data.get("password"):
            user.set_password(data["password"])

        if current_user.role == 'admin' and data.get("role"):
            user.role = data["role"]

        try:
            db.session.commit()
            return {"message": "User updated successfully"}
        except Exception as e:
            db.session.rollback()
            return {"message": "Error updating user", "error": str(e)}, 500

    @jwt_required()
    def delete(self, user_id):
        # Only allow admin to delete users or users to delete their own account
        current_user = User.query.get(get_jwt_identity())
        if current_user.id != user_id and current_user.role != 'admin':
            return {"message": "Unauthorized access"}, 403

        user = User.query.get_or_404(user_id)
        
        try:
            # Delete user's cart items first
            Cart.query.filter_by(user_id=user_id).delete()
            # Delete the user
            db.session.delete(user)
            db.session.commit()
            return {"message": "User deleted successfully"}
        except Exception as e:
            db.session.rollback()
            return {"message": "Error deleting user", "error": str(e)}, 500

