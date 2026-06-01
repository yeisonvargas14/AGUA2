from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        AGENCY = 'AGENCY', 'Agencia'
        CLIENT = 'CLIENT', 'Cliente'
        DRIVER = 'DRIVER', 'Repartidor'

    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.CLIENT)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    municipio = models.CharField(max_length=100, blank=True, help_text="Ej: Comarapa")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
