from django.contrib import admin
from .models import Promotion, AgencyPromotion

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_percentage', 'start_date', 'end_date', 'is_active', 'is_current')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')
    filter_horizontal = ('products',)

@admin.register(AgencyPromotion)
class AgencyPromotionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'valor', 'fecha_inicio', 'fecha_fin', 'activa', 'is_current')
    list_filter = ('activa', 'tipo', 'fecha_inicio', 'fecha_fin')
    search_fields = ('nombre', 'descripcion', 'condiciones')
    filter_horizontal = ('productos',)
