from django.urls import path
from . import views

urlpatterns = [
    # Cart URLs (new names)
    path('carrito/', views.view_cart, name='view_cart'),
    path('carrito/agregar/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('carrito/actualizar/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('carrito/eliminar/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),

    # Cart URLs (compatibility aliases)
    path('ver-carrito/', views.view_cart, name='ver_carrito'),
    path('agregar/<int:product_id>/', views.add_to_cart, name='agregar_al_carrito'),
    path('actualizar/<int:item_id>/', views.update_cart_item, name='actualizar_carrito'),
    path('eliminar/<int:item_id>/', views.remove_cart_item, name='eliminar_del_carrito'),
    path('carrito/aplicar-cupon/', views.aplicar_cupon, name='aplicar_cupon'),

    # Checkout URLs
    path('checkout/', views.checkout_paso1, name='checkout'), # alias to step 1
    path('checkout/paso1/', views.checkout_paso1, name='checkout_paso1'),
    path('checkout/paso2/', views.checkout_paso2, name='checkout_paso2'),
    path('pedido/<int:order_id>/ticket/', views.client_ticket, name='client_ticket'),
    path('validar-ubicacion/', views.validate_location, name='api_validar_ubicacion'),

    # Order history (two canonical names)
    path('historial/', views.historial_pedidos, name='historial_pedidos'),
    path('mis-pedidos/', views.client_orders, name='client_orders'),

    # Order detail
    path('pedido/<int:order_id>/', views.detalle_pedido, name='detalle_pedido'),

    path('cancelar/<int:order_id>/', views.cancelar_pedido, name='cancelar_pedido'),
    path('valorar/<int:order_id>/', views.valorar_pedido, name='valorar_pedido'),
]
