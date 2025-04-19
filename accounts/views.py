from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser,Category,Product,Cart,Wishlist,Order,OrderItem
from django import forms
from .forms import CategoryForm,ProductForm,ShippingForm,ProfileUpdateForm
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.db import models
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
import uuid,requests
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
    # Check if the user is an admin
    if not request.user.is_admin:
        return redirect('user_dashboard')
    
    # Fetch statistics for the dashboard
    total_users = CustomUser.objects.count()  # Total users
    total_products = Product.objects.count()  # Total products
    total_orders = Order.objects.count()  # Total orders
    pending_orders = Order.objects.filter(status='Pending').count()  # Pending orders

    # Additional statistics (e.g., low stock products, awaiting approval)
    # low_stock_products = Product.objects.filter(stock__lte=5).count()  # Low stock products (ensure you have a stock field in Product)
    awaiting_approval = CustomUser.objects.filter(is_active=False).count()  # Users awaiting approval

    # Fetch recent orders (optional)
    recent_orders = Order.objects.all().order_by('-order_date')  # Get 5 most recent orders

    # Sales Data (example for monthly sales)
    sales_labels = []  # To hold months (or any period you want)
    sales_data = []    # To hold the total sales for each month

     # Calculate sales for the past 4 months (adjust as needed)
    current_month = timezone.now().month
    for i in range(4):
        month = (current_month - i) % 12
        year = timezone.now().year
        if month == 0:
            month = 12
            year -= 1

        # Add month name to sales_labels
        sales_labels.append(datetime.datetime(year, month, 1).strftime('%B'))

        # Calculate the total sales for this month
        total_sales = Order.objects.filter(
            order_date__month=month,
            order_date__year=year
        ).aggregate(total_sales=models.Sum('total_price'))['total_sales'] or 0

        sales_data.append(total_sales)
    # Pass all the data to the template
    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        # 'low_stock_products': low_stock_products,
        'awaiting_approval': awaiting_approval,
        'recent_orders': recent_orders,
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
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect("cart")

    total_amount = sum(item.total_price() for item in cart_items)

    if request.method == "POST":
        form = ShippingForm(request.POST)
        if form.is_valid():
            shipping_address = form.cleaned_data["address"]
            order = Order.objects.create(
                user=request.user,
                total_price=total_amount,
                shipping_address=shipping_address,
            )

            # FIX: Add OrderItems with correct quantity
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity  # use cart quantity
                )

            cart_items.delete()
            return redirect("order_summary", order_id=order.id)
    else:
        form = ShippingForm()

    return render(request, "accounts/checkout.html", {
        "form": form,
        "total_amount": total_amount,
        "cart_items": cart_items,
    })


# Order Summary View
@login_required
def order_summary(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    context = {
        'order': order,
        'order_items': order_items,
        'total_price': order.total_price  # Use stored total_price directly
    }
    return render(request, 'accounts/order_summary.html', context)

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


@login_required
@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'accounts/user_orders.html', {'orders': orders})

@login_required
def admin_manage_orders(request):
    """Admin view to list all orders with filtering option."""
    if not request.user.is_admin:
        messages.error(request, "Unauthorized access!")
        return redirect("home")

    # Get the filter value from the GET request (if any)
    status_filter = request.GET.get('status_filter', '')

    # Apply filtering if a status filter is provided
    if status_filter:
        orders = Order.objects.filter(status=status_filter).order_by("-order_date")
    else:
        orders = Order.objects.all().order_by("-order_date")
    #paginator
    paginator=Paginator(orders,3)
    page=request.GET.get("page")
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    return render(request, "accounts/manage_orders.html", {"orders": orders, "status_filter": status_filter})

@login_required
def admin_order_detail(request, order_id):
    """Admin view to see order details."""
    if not request.user.is_admin:
        messages.error(request, "Unauthorized access!")
        return redirect("home")

    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    return render(request, "accounts/order_detail.html", {"order": order, "order_items": order_items})

@login_required
def admin_update_order_status(request, order_id):
    """Admin updates order status."""
    if not request.user.is_admin:
        messages.error(request, "Unauthorized access!")
        return redirect("home")

    order = get_object_or_404(Order, id=order_id)
    
    if request.method == "POST":
        new_status = request.POST.get("status")
        order.status = new_status
        order.save()
        messages.success(request, f"Order #{order.id} status updated to {new_status}.")
        return redirect("admin_manage_orders")
    
    return render(request, "accounts/update_order_status.html", {"order": order})