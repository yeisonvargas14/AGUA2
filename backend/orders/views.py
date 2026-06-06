from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
import json
from decimal import Decimal

from core.decorators import role_required
from products.models import Product
from coupons.models import Coupon
from ratings.models import Rating
from inventory.models import InventoryLog
from .models import Cart, CartItem, Order, OrderItem
from .cart_helpers import _get_or_create_cart
from core.geo import is_inside_comarapa
from core.pusher_service import notify_new_order


# ─────────────────────────────────────────────────────────────────────────────
# Cart Views — available for anonymous and authenticated users
# ─────────────────────────────────────────────────────────────────────────────

def ver_carrito(request):
    """Display the current cart contents (anonymous or logged-in)."""
    cart = _get_or_create_cart(request)

    # Coupon logic only available for authenticated clients
    coupon_id = request.session.get('applied_coupon_id')
    coupon = None
    discount = Decimal('0.00')

    if coupon_id and request.user.is_authenticated:
        try:
            coupon = Coupon.objects.get(id=coupon_id, user_client=request.user, used=False)
            if coupon.is_expired:
                del request.session['applied_coupon_id']
                coupon = None
                messages.warning(request, "El cupón aplicado ha expirado.")
            else:
                discount = cart.total_amount * (Decimal(str(coupon.discount_percentage)) / Decimal('100.00'))
        except Coupon.DoesNotExist:
            del request.session['applied_coupon_id']

    total = cart.total_amount - discount
    if total < 0:
        total = Decimal('0.00')

    return render(request, 'client/carrito.html', {
        'cart': cart,
        'coupon': coupon,
        'discount': discount,
        'total': total
    })


@require_POST
def agregar_al_carrito(request, product_id):
    """Add a product to cart — works for anonymous and authenticated users."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))

    if product.stock < quantity:
        messages.error(request, f"Lo sentimos, solo quedan {product.stock} unidades de {product.name}.")
        return redirect('landing')

    cart = _get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'price_at_time': product.price}
    )

    if not created:
        if cart_item.quantity + quantity > product.stock:
            messages.error(request, f"No puedes agregar más de {product.stock} unidades al carrito.")
            return redirect('ver_carrito')
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
        cart_item.price_at_time = product.price
    cart_item.save()

    messages.success(request, f"¡{product.name} agregado al carrito!")

    # After adding, redirect back to the landing page if not logged in
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '')
    if next_url:
        return redirect(next_url)
    return redirect('ver_carrito')


@require_POST
def actualizar_carrito(request, item_id):
    """Update quantity of a cart item."""
    cart = _get_or_create_cart(request)
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    else:
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        name = cart_item.product.name
        cart_item.delete()
        messages.info(request, f"{name} eliminado del carrito.")
    elif quantity > cart_item.product.stock:
        messages.error(request, f"Solo hay {cart_item.product.stock} unidades disponibles de {cart_item.product.name}.")
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"Cantidad de {cart_item.product.name} actualizada.")

    return redirect('ver_carrito')


@require_POST
def eliminar_del_carrito(request, item_id):
    """Remove an item from the cart."""
    cart = _get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    name = cart_item.product.name
    cart_item.delete()
    messages.info(request, f"{name} eliminado del carrito.")
    return redirect('ver_carrito')


@login_required
@role_required('client')
@require_POST
def aplicar_cupon(request):
    code = request.POST.get('code', '').strip().upper()
    cart = _get_or_create_cart(request)

    if not cart.items.exists():
        messages.error(request, "Tu carrito está vacío.")
        return redirect('ver_carrito')

    try:
        coupon = Coupon.objects.get(code=code, user_client=request.user, used=False)
        if coupon.is_expired:
            messages.error(request, "Este cupón ya ha expirado.")
        else:
            request.session['applied_coupon_id'] = coupon.id
            messages.success(request, f"¡Cupón '{code}' de {coupon.discount_percentage}% aplicado correctamente!")
    except Coupon.DoesNotExist:
        messages.error(request, "Cupón no válido o ya utilizado.")

    return redirect('ver_carrito')


# ─────────────────────────────────────────────────────────────────────────────
# Checkout — requires authentication (redirect anonymous to login first)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@role_required('client')
def checkout_view(request):
    cart = _get_or_create_cart(request)

    if not cart.items.exists():
        messages.error(request, "Tu carrito está vacío.")
        return redirect('client_dashboard')

    # Check for coupon in session
    coupon_id = request.session.get('applied_coupon_id')
    coupon = None
    discount = Decimal('0.00')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, user_client=request.user, used=False)
            discount = cart.total_amount * (Decimal(str(coupon.discount_percentage)) / Decimal('100.00'))
        except Coupon.DoesNotExist:
            del request.session['applied_coupon_id']

    total = cart.total_amount - discount
    if total < 0:
        total = Decimal('0.00')

    if request.method == 'POST':
        address = request.POST.get('delivery_address', '').strip()
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')

        if not address:
            messages.error(request, "Por favor ingresa una dirección de entrega.")
            return render(request, 'client/checkout.html', {'cart': cart, 'total': total, 'coupon': coupon})

        if not lat or not lng:
            messages.error(request, "Debes permitir la geolocalización o marcar tu ubicación en el mapa.")
            return render(request, 'client/checkout.html', {'cart': cart, 'total': total, 'coupon': coupon})

        # Validate Geolocation using point_in_polygon
        if not is_inside_comarapa(lat, lng):
            messages.error(request, "Error de Geolocalización: El servicio de entregas a domicilio solo está disponible dentro del municipio de Comarapa.")
            return render(request, 'client/checkout.html', {'cart': cart, 'total': total, 'coupon': coupon})

        # Verify stock check
        for item in cart.items.all():
            if item.product.stock < item.quantity:
                messages.error(request, f"Stock insuficiente para {item.product.name}. Solo quedan {item.product.stock} unidades.")
                return redirect('ver_carrito')

        # Create Order
        order = Order.objects.create(
            client=request.user,
            total_amount=total,
            discount_amount=discount,
            coupon=coupon,
            delivery_address=address,
            delivery_lat=Decimal(lat),
            delivery_lng=Decimal(lng),
            status=Order.Status.PENDING
        )

        # Move cart items to order items and deduct stock
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.price_at_time,
            )
            # Deduct stock
            item.product.stock -= item.quantity
            item.product.save()

            # Log inventory movement
            InventoryLog.objects.create(
                product=item.product,
                user=request.user,
                quantity=item.quantity,
                movement_type=InventoryLog.MovementType.OUT,
                reason=f"Descuento automático por pedido #{order.id}"
            )

        # Mark coupon as used
        if coupon:
            coupon.used = True
            coupon.save()
            del request.session['applied_coupon_id']

        # Clear Cart
        cart.items.all().delete()

        # Real-time Pusher Notification to drivers
        notify_new_order(order)

        messages.success(request, f"¡Pedido #{order.id} registrado exitosamente! Está pendiente de aceptación.")
        return redirect('historial_pedidos')

    from django.conf import settings as django_settings
    return render(request, 'client/checkout.html', {
        'cart': cart,
        'coupon': coupon,
        'discount': discount,
        'total': total,
        'google_maps_api_key': django_settings.GOOGLE_MAPS_API_KEY
    })


@login_required
def validate_location(request):
    """Ajax endpoint for validating location."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = data.get('lat')
            lng = data.get('lng')
            valid = is_inside_comarapa(lat, lng)
            return JsonResponse({'valid': valid})
        except Exception as e:
            return JsonResponse({'valid': False, 'error': str(e)}, status=400)
    return JsonResponse({'valid': False}, status=405)


@login_required
@role_required('client')
def historial_pedidos(request):
    orders = Order.objects.filter(client=request.user).order_by('-created_at')

    # Check if orders have been rated
    for order in orders:
        order.rated = Rating.objects.filter(order=order, user_client=request.user).exists()

    return render(request, 'client/mis_pedidos.html', {
        'orders': orders
    })


@login_required
@role_required('client')
@require_POST
def cancelar_pedido(request, order_id):
    order = get_object_or_404(Order, id=order_id, client=request.user)

    if order.status != Order.Status.PENDING:
        messages.error(request, "No se puede cancelar el pedido porque ya ha sido aceptado o procesado.")
    else:
        order.status = Order.Status.CANCELLED
        order.save()

        # Restock items
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()

            # Log restock movement
            InventoryLog.objects.create(
                product=item.product,
                user=request.user,
                quantity=item.quantity,
                movement_type=InventoryLog.MovementType.IN,
                reason=f"Devolución de stock por cancelación de pedido #{order.id}"
            )

        messages.success(request, "Pedido cancelado y stock devuelto exitosamente.")

    return redirect('historial_pedidos')


@login_required
@role_required('client')
def valorar_pedido(request, order_id):
    order = get_object_or_404(Order, id=order_id, client=request.user)

    if order.status != Order.Status.DELIVERED:
        messages.error(request, "Solo puedes valorar pedidos que hayan sido entregados.")
        return redirect('historial_pedidos')

    if Rating.objects.filter(order=order, user_client=request.user).exists():
        messages.warning(request, "Ya has valorado este pedido anteriormente.")
        return redirect('historial_pedidos')

    if request.method == 'POST':
        # Can rate products in the order, and driver
        driver_score = request.POST.get('driver_score')
        driver_comment = request.POST.get('driver_comment', '')

        # Rate driver
        if driver_score and order.driver:
            Rating.objects.create(
                user_client=request.user,
                order=order,
                driver=order.driver,
                score=int(driver_score),
                comment=driver_comment
            )

        # Rate products
        for item in order.items.all():
            prod_score = request.POST.get(f'product_score_{item.product.id}')
            prod_comment = request.POST.get(f'product_comment_{item.product.id}', '')
            if prod_score:
                Rating.objects.create(
                    user_client=request.user,
                    order=order,
                    product=item.product,
                    score=int(prod_score),
                    comment=prod_comment
                )

        messages.success(request, "¡Muchas gracias por tus valoraciones!")
        return redirect('historial_pedidos')

    return render(request, 'client/valorar.html', {
        'order': order
    })


@login_required
@role_required('client')
def detalle_pedido(request, order_id):
    """Show full order detail for the client who owns it."""
    order = get_object_or_404(Order, id=order_id, client=request.user)
    items = order.items.select_related('product').all()
    return render(request, 'client/detalle_pedido.html', {
        'order': order,
        'items': items,
    })


@login_required
@role_required('client')
def client_orders(request):
    """Alias for historial_pedidos — canonical URL /mis-pedidos/."""
    return historial_pedidos(request)

