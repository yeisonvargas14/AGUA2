from django.urls import path
from . import views

urlpatterns = [
    path('', views.driver_dashboard, name='driver_dashboard'),
    path('aceptar/<int:order_id>/', views.driver_accept_order, name='driver_accept_order'),
    path('actualizar/<int:order_id>/', views.driver_update_status, name='driver_update_status'),
    path('historial/', views.driver_history, name='driver_history'),
]
