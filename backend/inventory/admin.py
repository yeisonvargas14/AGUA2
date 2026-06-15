from django.contrib import admin
from .models import InventoryLog

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'user', 'reason', 'created_at')
    list_filter = ('movement_type', 'created_at', 'product')
    search_fields = ('product__name', 'reason', 'user__username')
