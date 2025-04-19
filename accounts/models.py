from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)
    profile_picture=models.ImageField(upload_to="profile_pictures/",default="profile_pictures/default.jpg")

class Category(models.Model):
    name=models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    name=models.CharField(max_length=255)
    description=models.TextField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    image=models.ImageField(upload_to='product_images/')

    def __str__(self):
        return self.name
    
class Cart(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.product.price*self.quantity

class Wishlist(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
    
class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Shipped", "Shipped"), ("Delivered", "Delivered")],
        default="Pending"
    )

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def item_total(self):
        return self.product.price * self.quantity