"""
Management command to create or reset the super administrator account.
Usage: python manage.py create_superadmin
"""
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Creates or resets the super administrator account with default credentials'

    # ─── Default credentials ───────────────────────────────
    SUPERADMIN_EMAIL = 'admin@purificadora.com'
    SUPERADMIN_PASSWORD = 'Admin2026!'
    SUPERADMIN_FIRST_NAME = 'Super'
    SUPERADMIN_LAST_NAME = 'Administrador'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email=self.SUPERADMIN_EMAIL,
            defaults={
                'username': 'superadmin',
                'first_name': self.SUPERADMIN_FIRST_NAME,
                'last_name': self.SUPERADMIN_LAST_NAME,
                'role': User.Roles.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )

        if not created:
            # Reset existing account to ensure access
            user.username = 'superadmin'
            user.first_name = self.SUPERADMIN_FIRST_NAME
            user.last_name = self.SUPERADMIN_LAST_NAME
            user.role = User.Roles.ADMIN
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()

        # Always set/reset password
        user.set_password(self.SUPERADMIN_PASSWORD)
        user.save()

        action = 'CREADO' if created else 'ACTUALIZADO'
        self.stdout.write(self.style.SUCCESS(
            f'\n==================================================='
            f'\n   Super Administrador {action}'
            f'\n==================================================='
            f'\n   Email:    {self.SUPERADMIN_EMAIL}'
            f'\n   Password: {self.SUPERADMIN_PASSWORD}'
            f'\n   Role:     Administrador'
            f'\n==================================================='
        ))
