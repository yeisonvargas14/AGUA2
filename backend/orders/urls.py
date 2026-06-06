from django.urls import path
from . import views

urlpatterns = [
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:product_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/aplicar-cupon/', views.aplicar_cupon, name='aplicar_cupon'),

    path('checkout/', views.checkout_view, name='checkout'),
    path('validar-ubicacion/', views.validate_location, name='api_validar_ubicacion'),

    # Order history (two canonical names)
    path('historial/', views.historial_pedidos, name='historial_pedidos'),
    path('mis-pedidos/', views.client_orders, name='client_orders'),

    # Order detail
    path('pedido/<int:order_id>/', views.detalle_pedido, name='detalle_pedido'),

    path('cancelar/<int:order_id>/', views.cancelar_pedido, name='cancelar_pedido'),
    path('valorar/<int:order_id>/', views.valorar_pedido, name='valorar_pedido'),
]
