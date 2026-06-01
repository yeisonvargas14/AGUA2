from django.db import models
from django.conf import settings
from products.models import Product

class InventoryLog(models.Model):
    class MovementType(models.TextChoices):
        IN = 'IN', 'Entrada'
        OUT = 'OUT', 'Salida'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    movement_type = models.CharField(max_length=3, choices=MovementType.choices)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} - {self.quantity}"
