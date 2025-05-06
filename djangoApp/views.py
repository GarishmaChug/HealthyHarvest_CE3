from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest

from .models import Product
from django.shortcuts import render, get_object_or_404
from .models import Product , Cart 
from .models import Cart, CartItem, Product


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        selected_role=request.POST.get('role')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if(selected_role=='admin' and user.is_superuser) or (selected_role=='user' and not user.is_superuser):
               login(request, user)
               messages.success(request, f"Welcome, {username}!")
               return redirect('dashboard')  
            else:
               messages.error(request,"invalid credentials or passsword")
        # or whatever your post-login page is
        else:
           messages.error(request, "Invalid username or password")

    return render(request, 'login.html')
 


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

        print("Password:", password)
        print("Confirm Password:", cpassword)

        if not password or not cpassword:
            messages.error(request, 'Password and Confirm Password are required')
        elif password != cpassword:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already used')
        else:
            try:
                validate_password(password)
                user = User.objects.create_user(
                    username=username, email=email, password=password)
                messages.success(request, 'Registration successful! You can now login.')
                return redirect('login')
            except ValidationError as e:
                for error in e:
                    messages.error(request, error)

    return render(request, 'register.html')


@login_required
def dashboard_view(request):
    return render(request,'dashboard.html')
@login_required
def profile_view(request):
    return render(request,'profile.html')
@login_required
def product_view(request):
    return render(request,'product.html')




def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return render(request,'home.html')

# Create your views here.
def home_view(request):
    return render(request , 'home.html')








def search(request):
    query = request.GET.get('query', '').lower()  # Get the search query from the URL
    print(f"Search Query: {query}")  # Debug: Show the search query
    if query:
        # Filter the products based on the search query (case insensitive)
        products = Product.objects.filter(name__icontains=query)
        print(f"Number of Products Found: {len(products)}")  # Debug: Show the number of products found
        print("Products found:", products)  # Debug: Show the actual products found
    else:
        # If no query is provided, return all products
        products = Product.objects.all()
        print(f"All Products: {products}")
    # Pass the query and products to the template
    return render(request, 'search_result.html', {'query': query, 'products': products})



@login_required
def profile_view(request):
    return render(request, 'profile.html')

def all_view(request):
    products = Product.objects.all()
    return render(request, 'all.html', {'products': products})

def pharmacy_view(request):
    products = Product.objects.filter(category='pharmacy')
    return render(request, 'pharmacy.html', {'products': products})

def fruits_view(request):
    products = Product.objects.filter(category='grocery')
    return render(request, 'fruits&veg.html', {'products': products})

def beauty_view(request):
    products = Product.objects.filter(category='beauty')
    return render(request, 'beauty.html', {'products': products})

def snacks_view(request):
    products = Product.objects.filter(category='snacks')
    return render(request, 'snacks.html', {'products': products})

def faq_view(request):
    return render(request, 'faq.html')

@login_required
def checkout_view(request):
    """
    Handles the checkout process and clears the cart after successful checkout.
    """
    try:
        # Get the user's cart
        cart = Cart.objects.get(user=request.user)
        
        # Get all cart items
        cart_items = CartItem.objects.filter(cart=cart)
        
        if request.method == 'POST':
            # Get form data
            delivery_address = request.POST.get('delivery_address')
            payment_method = request.POST.get('payment_method')
            
            if not delivery_address or not payment_method:
                messages.error(request, "Please fill in all required fields.")
                return redirect('checkout')
            
            if cart_items.exists():
                # Calculate total
                cart_total = sum(item.total_price for item in cart_items)
                
                # Here you would typically:
                # 1. Process the payment
                # 2. Create an order record
                # 3. Send confirmation email
                # For now, we'll just clear the cart
                
                # Clear the cart
                cart_items.delete()
                
                # Show success message with order total
                messages.success(request, f"Order placed successfully! Total: ${cart_total}")
                return redirect('home')
            else:
                messages.warning(request, "Your cart is empty. Add some items before checkout.")
                return redirect('cart')
            
        # If GET request, show checkout page
        if cart_items.exists():
            # Calculate total
            cart_total = sum(item.total_price for item in cart_items)
            
            context = {
                'cart_items': cart_items,
                'cart_total': cart_total,
            }
            return render(request, 'checkout.html', context)
        else:
            messages.warning(request, "Your cart is empty. Add some items before checkout.")
            return redirect('cart')
            
    except Cart.DoesNotExist:
        messages.warning(request, "You don't have a cart. Add some items first.")
        return redirect('cart')
    except Exception as e:
        messages.error(request, f"An error occurred during checkout: {str(e)}")
        return redirect('cart')

@login_required
def cart_view(request):
    """
    Displays the user's shopping cart.
    Ensures a cart exists for the user.
    """
    try:
        # Get or create cart for the user
        cart, created = Cart.objects.get_or_create(user=request.user)
        print(f"Cart ID: {cart.id}, Created: {created}")
        
        # Get all cart items with related product data
        cart_items = CartItem.objects.filter(cart=cart).select_related('product')
        print(f"Number of cart items: {cart_items.count()}")
        
        # Calculate total
        cart_total = sum(item.total_price for item in cart_items)
        print(f"Cart total: {cart_total}")
        
        # Debug print all items
        for item in cart_items:
            print(f"Item: {item.product.name}, Quantity: {item.quantity}, Price: {item.price}, Total: {item.total_price}")
        
        context = {
            'cart_items': cart_items,
            'cart_total': cart_total,
        }
        
        return render(request, 'cart.html', context)
        
    except Exception as e:
        print(f"Error in cart_view: {str(e)}")
        messages.error(request, "An error occurred while loading your cart.")
        return redirect('home')

@login_required
def add_to_cart(request, product_id):
    """
    Adds a product to the user's cart or increments its quantity.
    """
    try:
        # Get the product
        product = Product.objects.get(id=product_id)
        print(f"Adding product: {product.name} (ID: {product_id})")
        
        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        print(f"Cart ID: {cart.id}, Created: {created}")
        
        # Try to get existing cart item
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        
        if cart_item:
            # Item exists, increment quantity
            cart_item.quantity += 1
            cart_item.save()
            print(f"Updated quantity for {product.name} to {cart_item.quantity}")
            messages.success(request, f"Updated quantity for {product.name} in your cart.")
        else:
            # Create new cart item
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                price=product.price,
                quantity=1
            )
            print(f"Created new cart item for {product.name}")
            messages.success(request, f"Added {product.name} to your cart.")
        
        # Verify the item was added
        cart_items_count = CartItem.objects.filter(cart=cart).count()
        print(f"Total items in cart: {cart_items_count}")
        
        return redirect('cart')
        
    except Product.DoesNotExist:
        print(f"Product not found: {product_id}")
        messages.error(request, "Product not found.")
        return redirect('product_list')
    except Exception as e:
        print(f"Error in add_to_cart: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('product_list')

@login_required
def remove_from_cart(request, item_id):
    """
    Removes an item completely from the user's cart.
    """
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f"Removed {product_name} from your cart.")
    return redirect('cart')

@login_required
def update_cart_quantity(request, item_id):
    """
    Updates the quantity of a specific item in the cart via POST request.
    Handles both direct quantity input and plus/minus button actions.
    """
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        try:
            action = request.POST.get('action')
            if action == 'increase':
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, f"Added one more {cart_item.product.name} to your cart.")
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                    messages.success(request, f"Removed one {cart_item.product.name} from your cart.")
                else:
                    # If quantity is 1 and trying to decrease, remove the item
                    product_name = cart_item.product.name
                    cart_item.delete()
                    messages.success(request, f"Removed {product_name} from your cart.")
            else:
                # Handle direct quantity input
                quantity = int(request.POST.get('quantity'))
                if quantity > 0:
                    cart_item.quantity = quantity
                    cart_item.save()
                    messages.success(request, f"Updated quantity for {cart_item.product.name}.")
                elif quantity == 0:
                    # If quantity is set to 0, remove the item
                    product_name = cart_item.product.name
                    cart_item.delete()
                    messages.success(request, f"Removed {product_name} from your cart.")
                else:
                    messages.error(request, "Quantity must be a positive number.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")
        return redirect('cart')
    else:
        return HttpResponseBadRequest("Invalid request method.")

from django.shortcuts import render, get_object_or_404
from .models import Product

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})


def product_list(request):
    products=Product.objects.all()
    return render(request, 'beauty.html' , {'products': products})

# def product_detail_view(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     return render(request, 'product_detail.html', {'product': product})
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    return render(request, 'product_form.html', {'product': product})

def product_save(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, pk=product_id) if product_id else Product()

        product.name = request.POST['name']
        product.price = request.POST['price']
        product.description = request.POST['description']
        product.category = request.POST['category']

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()
        return redirect('product_list')
    return redirect('product_form')

def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('product_list')

from .models import Product

CATEGORY_CHOICES = Product.CATEGORY_CHOICES  # 👈 Import from model

def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    return render(request, 'product_form.html', {
        'product': product,
        'category_choices': CATEGORY_CHOICES  # 👈 Pass to template
    })

def terms(request):
    return render(request,'terms.html')
