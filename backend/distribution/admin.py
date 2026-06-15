from django.contrib import admin
from .models import Delivery

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('order', 'driver', 'assigned_at', 'delivered_at')
    list_filter = ('assigned_at', 'delivered_at')
    search_fields = ('order__id', 'driver__username', 'notes')
