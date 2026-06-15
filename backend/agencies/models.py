from django.db import models
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField

class Agency(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agencia'
    )
    nombre_empresa = models.CharField(max_length=200, default='')
    direccion = models.TextField(default='')
    telefono = models.CharField(max_length=20, default='')
    email_contacto = models.EmailField(default='')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    activa = models.BooleanField(default=True)
    notas_internas = models.TextField(blank=True)
    logo = CloudinaryField('logo', blank=True, null=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.nombre_empresa

    @property
    def manager(self):
        return self.usuario

    @property
    def name(self):
        return self.nombre_empresa

    @property
    def address(self):
        return self.direccion

    @property
    def is_active(self):
        return self.activa

