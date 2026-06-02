from django.db import models
from products.models import Product

class Promotion(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    discount_percentage = models.PositiveIntegerField(help_text="Porcentaje de descuento global para estos productos")
    products = models.ManyToManyField(Product, related_name='promotions')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.discount_percentage}%)"

    @property
    def is_current(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
