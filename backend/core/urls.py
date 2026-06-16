from django.urls import path
from . import views

urlpatterns = [
    # Admin Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Products CRUD
    path('productos/', views.admin_products, name='admin_products'),
    path('productos/nuevo/', views.admin_product_create, name='admin_product_create'),
    path('productos/editar/<int:pk>/', views.admin_product_edit, name='admin_product_edit'),
    path('productos/eliminar/<int:pk>/', views.admin_product_delete, name='admin_product_delete'),
    
    # Users CRUD
    path('usuarios/', views.admin_users, name='admin_users'),
    path('usuarios/nuevo/', views.admin_user_create, name='admin_user_create'),
    path('usuarios/editar/<int:pk>/', views.admin_user_edit, name='admin_user_edit'),
    path('usuarios/eliminar/<int:pk>/', views.admin_user_delete, name='admin_user_delete'),
    
    # Coupons CRUD
    path('cupones/', views.admin_coupons, name='admin_coupons'),
    path('cupones/nuevo/', views.admin_coupon_create, name='admin_coupon_create'),
    path('cupones/eliminar/<int:pk>/', views.admin_coupon_delete, name='admin_coupon_delete'),
    
    # Promotions CRUD
    path('promociones/', views.admin_promotions, name='admin_promotions'),
    path('promociones/nuevo/', views.admin_promotion_create, name='admin_promotion_create'),
    path('promociones/eliminar/<int:pk>/', views.admin_promotion_delete, name='admin_promotion_delete'),
    
    # Orders Management
    path('pedidos/', views.admin_orders, name='admin_orders'),
    path('pedidos/detalle/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('pedidos/<int:pk>/asignar/', views.admin_assign_driver, name='admin_assign_driver'),
    path('pedidos/<int:pk>/cancelar/', views.admin_cancel_order, name='admin_cancel_order'),
    path('pedidos/<int:pk>/ticket/', views.admin_print_ticket, name='pedido_ticket'),
    path('pedidos/ticket/<int:pk>/', views.admin_print_ticket, name='admin_print_ticket'),
    
    # Notifications APIs
    path('api/nuevos-pedidos/contador/', views.api_nuevos_pedidos_contador, name='api_nuevos_pedidos_contador'),
    path('api/nuevos-pedidos/marcar-vistos/', views.api_nuevos_pedidos_marcar_vistos, name='api_nuevos_pedidos_marcar_vistos'),
    
    # Reports
    path('reportes/', views.admin_reports, name='admin_reports'),

    # Agencies Management
    path('agencias/', views.admin_agencies, name='admin_agencies'),
    path('agencias/nueva/', views.admin_agency_create, name='admin_agency_create'),
    path('agencias/<int:pk>/', views.admin_agency_detail, name='admin_agency_detail'),
    path('agencias/<int:pk>/editar/', views.admin_agency_edit, name='admin_agency_edit'),
    path('agencias/<int:pk>/toggle/', views.admin_agency_toggle_active, name='admin_agency_toggle_active'),

    # Repartidores (Drivers) Management
    path('repartidores/', views.admin_drivers, name='admin_drivers'),
    path('repartidores/crear/', views.admin_driver_create, name='admin_driver_create'),
    path('repartidores/editar/<int:pk>/', views.admin_driver_edit, name='admin_driver_edit'),
    path('repartidores/toggle/<int:pk>/', views.admin_driver_toggle, name='admin_driver_toggle_active'),
    path('repartidores/historial/<int:pk>/', views.admin_driver_history, name='admin_driver_history'),
]
