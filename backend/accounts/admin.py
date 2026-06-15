from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PasswordResetCode, DriverProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'telefono', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Información de Rol y Contacto', {'fields': ('role', 'telefono', 'address', 'municipio', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información de Rol y Contacto', {'fields': ('role', 'telefono', 'address', 'municipio', 'avatar')}),
    )

@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefono', 'codigo', 'creado_en', 'expira_en', 'usado')
    list_filter = ('usado', 'creado_en')
    search_fields = ('telefono', 'codigo', 'user__username')

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle', 'phone', 'active', 'rating_avg')
    list_filter = ('vehicle', 'active')
    search_fields = ('user__username', 'phone')
