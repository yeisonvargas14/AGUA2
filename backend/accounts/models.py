from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        AGENCY = 'agency', 'Agencia'
        CLIENT = 'client', 'Cliente'
        DRIVER = 'driver', 'Repartidor'

    role = models.CharField(
        max_length=15,
        choices=Roles.choices,
        default=Roles.CLIENT
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    municipio = models.CharField(max_length=100, blank=True, help_text="Ej: Comarapa")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
