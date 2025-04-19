from django import forms
from .models import Category,Product,CustomUser

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class ProductForm(forms.ModelForm):
    class Meta:
        model=Product
        fields=['name','description','price','category','image']


class ShippingForm(forms.Form):
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Enter shipping address"}))

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model=CustomUser
        fields = ['username', 'email', 'profile_picture']