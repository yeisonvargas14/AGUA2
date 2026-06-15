from django.contrib import admin
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'user_client', 'discount_percentage', 'expires_at', 'used', 'created_at')
    list_filter = ('used', 'expires_at', 'created_at')
    search_fields = ('code', 'user_client__username')
