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


class AgencyPromotion(models.Model):
    TIPO_CHOICES = [
        ('descuento_porcentaje', 'Descuento Porcentual'),
        ('descuento_fijo', 'Descuento Fijo'),
        ('combo', 'Combo (Pague X Lleve Y)'),
        ('volumen', 'Descuento por Volumen (Cantidad Mínima)'),
    ]

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2, help_text="Valor del descuento (porcentaje o monto fijo) o cantidad a regalar en combos/volumen")
    productos = models.ManyToManyField(Product, blank=True, related_name='agency_promotions', help_text="Productos a los que aplica. Si está vacío, aplica a todo el catálogo")
    condiciones = models.TextField(blank=True, null=True, help_text="Descripción de condiciones de la promoción para el usuario")
    cantidad_minima = models.PositiveIntegerField(default=1, help_text="Cantidad mínima requerida en el carrito del producto (o total de productos si aplica a todo) para activar la promoción")
    cantidad_regalo = models.PositiveIntegerField(default=0, help_text="Para combos/volumen, cantidad de unidades que se regalan (ej. lleva 1 gratis)")
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    @property
    def is_current(self):
        from django.utils import timezone
        now = timezone.now()
        return self.activa and self.fecha_inicio <= now <= self.fecha_fin

