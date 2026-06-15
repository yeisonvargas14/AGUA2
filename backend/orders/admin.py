from django.contrib import admin
from .models import Cart, CartItem, AgencyCart, AgencyCartItem, Order, OrderItem, OrderLog

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'created_at', 'updated_at', 'total_amount')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'session_key')
    inlines = [CartItemInline]

class AgencyCartItemInline(admin.TabularInline):
    model = AgencyCartItem
    extra = 0

@admin.register(AgencyCart)
class AgencyCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'agency', 'created_at', 'updated_at', 'total_amount')
    list_filter = ('created_at',)
    search_fields = ('agency__nombre_empresa',)
    inlines = [AgencyCartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderLogInline(admin.TabularInline):
    model = OrderLog
    extra = 0
    readonly_fields = ('timestamp',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'agency', 'driver', 'status', 'tipo_pedido', 'total_amount', 'discount_amount', 'fecha_entrega_deseada', 'created_at')
    list_filter = ('status', 'tipo_pedido', 'created_at', 'fecha_entrega_deseada')
    search_fields = ('id', 'client__username', 'agency__nombre_empresa', 'delivery_address')
    inlines = [OrderItemInline, OrderLogInline]
