from django.contrib import admin
from .models import DeliveryPersonApplication

class DeliveryPersonApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'status', 'applied_on')
    list_filter = ('status', 'applied_on')
    search_fields = ('name', 'email', 'phone')

admin.site.register(DeliveryPersonApplication, DeliveryPersonApplicationAdmin)
