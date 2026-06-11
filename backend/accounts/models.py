from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN    = 'admin',    'Administrador'
        VENDEDOR = 'vendedor', 'Vendedor'
        AGENCY   = 'agency',   'Agencia'
        CLIENT   = 'client',   'Cliente'
        DRIVER   = 'driver',   'Repartidor'

    role = models.CharField(
        max_length=15,
        choices=Roles.choices,
        default=Roles.CLIENT
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Celular",
        help_text="Número de celular de contacto"
    )
    email = models.EmailField(
        unique=True,
        blank=True,
        null=True,
        verbose_name="Correo electrónico"
    )
    address = models.CharField(max_length=255, blank=True)
    municipio = models.CharField(max_length=100, blank=True, help_text="Ej: Comarapa")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    @property
    def full_name(self):
        """Returns the first_name and last_name joined by space, or email if not set."""
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"


class PasswordResetCode(models.Model):
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='password_reset_codes'
    )
    telefono = models.CharField(max_length=20)
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=['telefono', 'codigo'])]
        verbose_name = 'Código de Recuperación'
        verbose_name_plural = 'Códigos de Recuperación'

    def __str__(self):
        return f"Código {self.codigo} para {self.telefono}"

    def is_valid(self):
        from django.utils import timezone
        return (not self.usado) and (timezone.now() <= self.expira_en)


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


