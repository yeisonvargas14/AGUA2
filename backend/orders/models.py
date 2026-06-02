from django.db import models
from django.conf import settings
from products.models import Product

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.user.username}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} en carrito"

    @property
    def subtotal(self):
        return self.product.price * self.quantity

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        ACCEPTED = 'accepted', 'Aceptado'
        ON_WAY = 'on_way', 'En camino'
        DELIVERED = 'delivered', 'Entregado'
        CANCELLED = 'cancelled', 'Cancelado'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_orders',
        limit_choices_to={'role': 'client'}
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driver_orders',
        limit_choices_to={'role': 'driver'}
    )
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agency_orders'
    )
    coupon = models.ForeignKey(
        'coupons.Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_in_orders'
    )
    
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.CharField(max_length=255, blank=True)
    delivery_lat = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    delivery_lng = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.client.username} - {self.get_status_display()}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Pedido #{self.order.id})"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
