from django.db import models
from django.conf import settings
from products.models import Product

class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Carrito de {self.user.username}"
        return f"Carrito anónimo ({self.session_key})"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} en carrito"

    @property
    def subtotal(self):
        # Prefer the new price field, fallback to price_at_time
        p = self.price if self.price > 0 else self.price_at_time
        return p * self.quantity

    def save(self, *args, **kwargs):
        if not self.price and self.product:
            self.price = self.product.price
        if not self.price_at_time and self.product:
            self.price_at_time = self.product.price
        super().save(*args, **kwargs)

class AgencyCart(models.Model):
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.CASCADE,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito Agencia de {self.agency.nombre_empresa}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())

class AgencyCartItem(models.Model):
    cart = models.ForeignKey(AgencyCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} en carrito agencia"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if not self.price and self.product:
            self.price = self.product.get_agency_price
        super().save(*args, **kwargs)


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
    
    fecha_entrega_deseada = models.DateField(null=True, blank=True)
    tipo_pedido = models.CharField(
        max_length=15,
        choices=[('cliente', 'Cliente'), ('agencia', 'Agencia')],
        default='cliente'
    )
    visto_admin = models.BooleanField(default=False)
    
    # Presencial / Venta Directa Fields
    origen = models.CharField(
        max_length=20,
        choices=[('venta_directa', 'Venta Directa'), ('pedido_online', 'Pedido Online')],
        default='pedido_online'
    )
    tipo_venta = models.CharField(
        max_length=20,
        choices=[('presencial', 'Presencial'), ('online', 'Online')],
        default='online'
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendedor_sales',
        limit_choices_to={'role': 'vendedor'}
    )
    metodo_pago = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[('efectivo', 'Efectivo'), ('transferencia', 'Transferencia'), ('tarjeta', 'Tarjeta')]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def subtotal(self):
        return self.total_amount + self.discount_amount

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

class OrderLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='logs')
    estado_anterior = models.CharField(max_length=15, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=15)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    nota = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pedido #{self.order.id} cambio: {self.estado_anterior} -> {self.estado_nuevo} en {self.timestamp}"
