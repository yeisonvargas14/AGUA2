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
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Nombre de usuario"
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    municipio = models.CharField(max_length=100, blank=True, help_text="Ej: Comarapa")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Username is no longer required for superusers by default, email is main field

    @property
    def full_name(self):
        """Returns the first_name and last_name joined by space, or email if not set."""
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"


class DriverProfile(models.Model):
    VEHICLE_CHOICES = [
        ('moto', 'Motocicleta'),
        ('auto', 'Automóvil'),
        ('bicicleta', 'Bicicleta'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )
    vehicle = models.CharField(
        max_length=20,
        choices=VEHICLE_CHOICES,
        default='moto'
    )
    phone = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=True)
    rating_avg = models.FloatField(default=0.0)
    current_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"Perfil de Repartidor: {self.user.full_name} ({self.get_vehicle_display()})"


