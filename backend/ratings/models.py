from django.db import models
from django.conf import settings
from orders.models import Order
from products.models import Product

class Rating(models.Model):
    user_client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings_made',
        limit_choices_to={'role': 'client'}
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='ratings',
        null=True,
        blank=True
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='driver_ratings',
        limit_choices_to={'role': 'driver'},
        null=True,
        blank=True
    )
    score = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = f"Producto: {self.product.name}" if self.product else f"Repartidor: {self.driver.username}"
        return f"Valoración de {self.user_client.username} ({self.score} estrellas) para {target}"
