from django.db import models
from django.conf import settings

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    user_client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='personal_coupons',
        limit_choices_to={'role': 'client'}
    )
    discount_percentage = models.PositiveIntegerField(help_text="Porcentaje de descuento (ej: 15 para 15%)")
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.discount_percentage}% (Para: {self.user_client.username})"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
