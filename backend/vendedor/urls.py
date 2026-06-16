from django.urls import path
from . import views

urlpatterns = [
    path('', views.vendedor_dashboard, name='vendedor_dashboard'),
    path('clientes/', views.vendedor_clients, name='vendedor_clients'),
    path('clientes/nuevo/', views.vendedor_client_create, name='vendedor_client_create'),
    path('clientes/editar/<int:pk>/', views.vendedor_client_edit, name='vendedor_client_edit'),
    path('pedidos/', views.vendedor_orders, name='vendedor_orders'),
    path('pedidos/nuevo/', views.vendedor_order_create, name='vendedor_order_create'),
    path('pedidos/<int:pk>/', views.vendedor_order_detail, name='vendedor_order_detail'),
    path('pedidos/<int:pk>/cancelar/', views.vendedor_order_cancel, name='vendedor_order_cancel'),
    path('pedidos/<int:pk>/asignar/', views.vendedor_assign_driver, name='vendedor_assign_driver'),
    path('catalogo/', views.vendedor_catalog, name='vendedor_catalog'),
    path('registrar-venta/', views.registrar_venta, name='registrar_venta'),
    path('buscar-clientes/', views.buscar_clientes_venta, name='buscar_clientes_venta'),
    path('crear-cliente-rapido/', views.crear_cliente_rapido_venta, name='crear_cliente_rapido_venta'),
    path('pedidos/<int:pk>/ticket/', views.vendedor_order_ticket, name='vendedor_order_ticket'),
]
