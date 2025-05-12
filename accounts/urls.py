from django.urls import path
from .views import (
    signup, user_login, admin_login, logout_view,
    user_dashboard, admin_dashboard, index,
    add_category, manage_categories,user_list,delete_user,add_product,manage_products,category_products,
    product_detail,view_cart,view_wishlist,add_to_cart,add_to_wishlist,remove_from_cart,update_cart,remove_from_wishlist,
    move_to_cart,edit_category,edit_product,delete_category,delete_product,
)
from accounts import views
urlpatterns = [
    path('', index, name='index'),
    path('signup/', signup, name='signup'),
    path('user_login/', user_login, name='user_login'),
    path('login/', user_login, name='login'),
    path('admin_login/', admin_login, name='admin_login'),
    path('logout/', logout_view, name='logout'),
    path('user_dashboard/', user_dashboard, name='user_dashboard'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('categories/add/', add_category, name='add_category'),
    path('categories/manage/', manage_categories, name='manage_categories'),
    path('edit-category/<int:category_id>/', edit_category, name='edit_category'),
    path('delete-category/<int:category_id>/', delete_category, name='delete_category'),
    path('category/<int:category_id>/', category_products, name='category_products'),
    path('users/',user_list,name='user_list'),
    path('users/delete/<int:user_id>/', delete_user, name='delete_user'),
    path("add_product/", add_product, name="add_product"),
    path("manage_products/", manage_products, name="manage_products"),
    path('edit-product/<int:product_id>/', edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', delete_product, name='delete_product'),
    path('product_detail/<int:product_id>/', product_detail, name='product_detail'),
    path("cart/", view_cart, name="cart"),
    path("cart/add/<int:product_id>/", add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:product_id>/", remove_from_cart, name="remove_from_cart"),
    path("cart/update/<int:product_id>/", update_cart, name="update_cart"),
    
    path("wishlist/", view_wishlist, name="wishlist"),
    path("wishlist/add/<int:product_id>/", add_to_wishlist, name="add_to_wishlist"),
    path("wishlist/remove/<int:product_id>/", remove_from_wishlist, name="remove_from_wishlist"),
    path("wishlist/move-to-cart/<int:product_id>/", move_to_cart, name="move_to_cart"),
    #Checkout
    path('checkout/', views.proceed_to_checkout, name='proceed_to_checkout'),
    path('order-summary/<int:order_id>/', views.order_summary, name='order_summary'),
    #Payment
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment_success/<str:order_id>/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    #User Order
    path('my-orders/', views.user_orders, name='user_orders'),
    path("profile/", views.profile_view, name="profile"),
    #Manage Order
    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('admin/orders/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
]
