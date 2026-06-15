from django.contrib import admin
from .models import Agency

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('nombre_empresa', 'usuario', 'telefono', 'email_contacto', 'activa', 'fecha_creacion')
    list_filter = ('activa', 'fecha_creacion')
    search_fields = ('nombre_empresa', 'usuario__username', 'telefono', 'email_contacto')
