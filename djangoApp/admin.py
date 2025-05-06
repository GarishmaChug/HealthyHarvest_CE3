
# Register your models here.
# from django.contrib import admin
# from .models import Product

# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['name', 'price', 'available']
#     search_fields = ['name']

# admin.site.register(Product)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin



from .models import Product

admin.site.register(Product)
