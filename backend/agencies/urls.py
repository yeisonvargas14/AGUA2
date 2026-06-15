from django.urls import path
from . import views

urlpatterns = [
    path('', views.agency_dashboard, name='agency_dashboard'),
    path('catalogo/', views.agency_catalog, name='agency_catalog'),
    path('carrito/', views.agency_cart, name='agency_cart'),
    path('carrito/agregar/<int:product_id>/', views.agency_add_to_cart, name='agency_add_to_cart'),
    path('checkout/', views.agency_checkout, name='agency_checkout'),
    path('pedidos/', views.agency_orders, name='agency_orders'),
    path('promociones/', views.agency_promotions, name='agency_promotions'),
    path('pedido/<int:order_id>/ticket/', views.agency_ticket, name='agency_ticket'),
    path('cambiar-contrasena/', views.agency_change_password, name='agency_change_password'),
]
