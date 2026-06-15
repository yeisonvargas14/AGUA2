from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user_client', 'order', 'product', 'driver', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('user_client__username', 'comment', 'product__name', 'driver__username')
