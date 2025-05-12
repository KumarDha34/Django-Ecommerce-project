from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser,Category,Product,Cart,Wishlist,Order,OrderItem,Payment
from django import forms
from .forms import CategoryForm,ProductForm,ShippingForm,ProfileUpdateForm
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.db import models
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
import uuid,requests
from django.conf import settings
from decimal import Decimal
# Index View (Home Page)
def index(request):
    return render(request, 'accounts/index.html')

# Signup Form
class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

# Admin Login Form
class AdminLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

# Signup View
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Signup successful! Please log in.")
            return redirect('user_login')
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})

# User Login View
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and not user.is_admin:
            login(request, user)
            return redirect('user_dashboard')
        else:
            messages.error(request, "Invalid credentials or not a user account")
    return render(request, 'accounts/user_login.html')

# Admin Login View
def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and user.is_admin:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not an admin account")
    return render(request, 'accounts/admin_login.html')

# User Dashboard
@login_required
def user_dashboard(request):
    categories=Category.objects.all()
    products=Product.objects.all()

    query=request.GET.get("search")
    category_filter=request.GET.get("category")
    if query:
        products=products.filter(name__icontains=query)
    if category_filter:
        products=products.filter(category_id=category_filter)
    
    #paginator
    paginator=Paginator(products,3)
    page=request.GET.get("page")
    try:
        products=paginator.page(page)
    except PageNotAnInteger:
        products=paginator.page(1)
    except EmptyPage:
        products=paginator.page(paginator.num_pages)
    return render(request, 'accounts/user_dashboard.html', {"categories": categories, "products": products})

@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        return redirect('user_dashboard')

    total_users = CustomUser.objects.filter(is_admin=False).count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Pending').count()
    shipped_products = Order.objects.filter(status='Shipped').count()
    delivered_products = Order.objects.filter(status='Delivered').count()
    awaiting_approval = CustomUser.objects.filter(is_active=False).count()
    recent_orders = Order.objects.order_by('-order_date')[:5]

    # Sales data for chart (last 4 months)
    sales_labels = []
    sales_data = []
    current_date = timezone.now()

    for i in range(3, -1, -1):
        date = current_date - datetime.timedelta(days=30 * i)
        month = date.month
        year = date.year
        label = datetime.datetime(year, month, 1).strftime('%B')

        total_sales = Order.objects.filter(
            order_date__month=month,
            order_date__year=year
        ).aggregate(total=models.Sum('total_price'))['total'] or 0

        sales_labels.append(label)
        sales_data.append(float(total_sales))

    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'sales_labels': sales_labels,
        'sales_data': sales_data,
    }

    return render(request, 'accounts/admin_dashboard.html', context)

# Logout View
def logout_view(request):
    logout(request)
    return redirect('user_login')

@login_required
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_categories')
    else:
        form = CategoryForm()
    return render(request, 'accounts/add_category.html', {'form': form})
@login_required
def manage_categories(request):
    categories = Category.objects.all()
    query = request.GET.get("search")
    
    if query:
        categories = categories.filter(name__icontains=query)

    # Pagination
    paginator = Paginator(categories, 3)  # Show 8 categories per page
    page = request.GET.get("page")

    try:
        categories = paginator.page(page)
    except PageNotAnInteger:
        categories = paginator.page(1)
    except EmptyPage:
        categories = paginator.page(paginator.num_pages)

    return render(request, 'accounts/manage_categories.html', {'categories': categories})

# Edit Category
@login_required
def edit_category(request,category_id):
    category=get_object_or_404(Category,id=category_id)
    if request.POST=="POST":
        form=CategoryForm(request.POST,instance=category)
        if form.is_valid():
            form.save()
            messages.success(request,"CAtegory Updated successfully!")
            return redirect("manage_categories")
    else:
        form=CategoryForm(instance=category)
    return render(request,'accounts/edit_category.html',{'form':form})

#Delete Category
@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully!")
        return redirect("manage_categories")

    return render(request, "accounts/delete_category.html", {"category": category})

# user list
@login_required
def user_list(request):
    users = CustomUser.objects.filter(is_admin=False)

    # Pagination
    paginator = Paginator(users, 3)  # Show 10 users per page
    page = request.GET.get("page")

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == "POST":
        user.delete()
        return redirect("user_list")

    return render(request, "accounts/delete_user.html", {"user": user})


# Add products
@login_required
def add_product(request):
    categories=Category.objects.all()
    if request.method=="POST":
        form=ProductForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect("manage_products")
    else:
        form=ProductForm()
    return render(request,'accounts/add_product.html',{"form":form,"categories":categories})

@login_required
def manage_products(request):
    query = request.GET.get("search")
    category_filter = request.GET.get("category")
    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)
    if category_filter:
        products = products.filter(category_id=category_filter)

    # Pagination
    paginator = Paginator(products, 4)  # Show 10 products per page
    page = request.GET.get("page")

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    categories = Category.objects.all()
    return render(request, 'accounts/manage_products.html', {
        'products': products,
        'categories': categories
    })

# Edit Product
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('manage_products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'accounts/edit_product.html', {'form': form, 'product': product})

#Delete Product

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect("manage_products")

    return render(request, "accounts/delete_product.html", {"product": product})

@login_required
def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'accounts/category_products.html', {'category': category, 'products': products})

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "accounts/product_detail.html", {"product": product})

# View Cart
@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.total_price() for item in cart_items)
    return render(request, "accounts/cart.html", {"cart_items": cart_items, "total_amount": total_amount})

# Add to Cart
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))  # Ensure quantity is provided, default to 1

    # Check if the user already has this product in the cart
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)

    if not created:  # If the item already exists in the cart, update the quantity
        cart_item.quantity += quantity  # Add the new quantity
        cart_item.save()
    else:
        cart_item.quantity = quantity  # Set the quantity if it's a new item
        cart_item.save()

    return redirect('cart')  # Redirect back to the cart page

# Remove from Cart
@login_required
def remove_from_cart(request, product_id):
    cart_item = get_object_or_404(Cart, user=request.user, product_id=product_id)
    cart_item.delete()
    return redirect("cart")

# Update Cart Quantity
@login_required
def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        cart_item = Cart.objects.get(user=request.user, product_id=product_id)
        cart_item.quantity = quantity
        cart_item.save()

        # 🔍 Log the updated quantity
        print(f"[Cart Update] User: {request.user.username}, Product: {cart_item.product.name}, Quantity: {cart_item.quantity}")

    return redirect('cart')

# View Wishlist
@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, "accounts/wishlist.html", {"wishlist_items": wishlist_items})

# Add to Wishlist
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect("wishlist")

# Remove from Wishlist
@login_required
def remove_from_wishlist(request, product_id):
    wishlist_item = get_object_or_404(Wishlist, user=request.user, product_id=product_id)
    wishlist_item.delete()
    return redirect("wishlist")

# Move from Wishlist to Cart
@login_required
def move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Remove from wishlist
    Wishlist.objects.filter(user=request.user, product=product).delete()

    # Add to cart
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect("cart")

@login_required
def proceed_to_checkout(request):
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart')  # Replace 'cart' with your cart URL name

    # Calculate total amount
    total_amount = sum(item.total_price() for item in cart_items)

    if request.method == "POST":
        address = request.POST.get("address")
        if not address:
            messages.error(request, "Please provide a shipping address.")
            return redirect('cart')

        # Temporarily store order information in session
        request.session['order_data'] = {
            'total_amount': str(total_amount),
            'address': address,
            'cart_items': list(cart_items.values('product_id', 'quantity'))  # Store necessary data
        }

        # Redirect to payment page
        return redirect('initiate_payment')

    return render(request, 'accounts/checkout.html', {'cart_items': cart_items, 'total_amount': total_amount})

@login_required
def order_summary(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order)

    return render(request, 'accounts/order_summary.html', {
        'order': order,
        'items': items
    })

#Payment
SECRET_KEY = "8gBm/:&EnhH.1/q"

import time
from .utils import generate_signature 
@login_required
def initiate_payment(request):
    # Fetch the user's cart
    cart = Cart.objects.filter(user=request.user)

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('user_dashboard')

    # Calculate the total price of the cart items
    total_price = sum(item.product.price * item.quantity for item in cart)

    # Create a temporary order and store it in the session for tracking
    transaction_uuid = f"ORDER{uuid.uuid4()}_{int(time.time())}"

    request.session['order_temp'] = {
        'total_price': str(total_price),  # Convert to string to avoid Decimal issue
        'transaction_uuid': transaction_uuid,
        'cart_items': list(cart.values('product', 'quantity'))  # Storing cart items temporarily
    }

    # Generate the eSewa payment signature
    signature = generate_signature(
        SECRET_KEY,
        total_price,
        transaction_uuid,
        "EPAYTEST"
    )

    # Convert total_price to a string with 2 decimal places for proper formatting
    total_price_str = str(total_price.quantize(Decimal('0.00')))  # Ensure it's formatted correctly

    params = {
        'amt': total_price_str,  # Ensure amt is a string
        'txAmt': '0',  # Transaction amount
        'psc': '0',    # Payment service charge
        'pdc': '0',    # Payment delivery charge
        'tAmt': total_price_str,  # Total amount as string
        'pid': transaction_uuid,
        'scd': 'EPAYTEST',  # Merchant code
        'su': f"http://localhost:8000/accounts/payment_success/{transaction_uuid}/",
        'fu': f"http://localhost:8000/accounts/payment_failure/",
        'signature': signature,
    }

    return render(request, 'accounts/payment_form.html', params)


@login_required
def payment_success(request, order_id):
    try:
        # Fetch order data from session (pending order)
        temp_order = request.session.get('order_data')  # Use 'order_data' instead of 'order_temp'
        if not temp_order:
            messages.error(request, "Invalid order session.")
            return redirect('user_dashboard')

        amt = request.GET.get('amt')  # Amount paid
        refId = request.GET.get('refId')  # Transaction reference ID

        if amt and refId:
            # Now, create the actual order and save it in the database
            order = Order(
                user=request.user,
                shipping_address=temp_order.get('address', ''),  # Retrieve address from session
                total_price=temp_order['total_amount'],
                status="Confirmed",  # Mark it as confirmed because payment is successful
                transaction_code=order_id
            )
            order.save()

            # Add order items
            for cart_item in temp_order['cart_items']:
                OrderItem.objects.create(
                    order=order,
                    product_id=cart_item['product_id'],  # Assuming you stored product_id in session
                    quantity=cart_item['quantity']
                )

            # Save payment details in the database
            Payment.objects.create(
                order=order,
                payment_method="eSewa",
                transaction_id=refId,
                amount=amt,
                payment_status="Paid"
            )

            # Clear session data since the order is finalized
            del request.session['order_data']

            # Clear the cart items
            Cart.objects.filter(user=request.user).delete()

            messages.success(request, "Payment successful!")

            return render(request, 'accounts/payment_success.html', {
                'order': order,
                'booking_code': order_id
            })

    except Exception as e:
        print(f"[Error] Payment failure: {e}")
        messages.error(request, "Invalid order code or payment failed.")
        return redirect('user_dashboard')

    return render(request, 'accounts/payment_success.html', {
        'order': order,
        'booking_code': order_id
    })
    


@login_required
def payment_failure(request):
    messages.error(request, "Payment failed. Please try again.")
    return redirect('user_dashboard')


@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'accounts/user_orders.html', {'orders': orders})

@login_required
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
    else:
        form = ProfileUpdateForm(instance=user)
    
    return render(request, "accounts/profile.html", {"form": form, "user": user})

def admin_orders(request):
    orders = Order.objects.select_related('user').order_by('-order_date')
    return render(request, 'accounts/admin_orders.html', {'orders': orders})


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order)
    payment = Payment.objects.filter(order=order).first()
    return render(request, 'accounts/order_detail.html', {
        'order': order,
        'items': items,
        'payment': payment,
    })

def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        status = request.POST.get('status')
        if status in ['Pending', 'Shipped', 'Delivered']:
            order.status = status
            order.save()
            messages.success(request, f'Order status updated to {status}')
        else:
            messages.error(request, 'Invalid status.')
    return redirect('order_detail', order_id=order_id)