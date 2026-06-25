from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
import json
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import authenticate, login, get_user_model

from core.decorators import role_required
from products.models import Product
from coupons.models import Coupon
from ratings.models import Rating
from inventory.models import InventoryLog
from .models import Cart, CartItem, Order, OrderItem, OrderLog
from .cart_helpers import _get_or_create_cart, transfer_cart
from core.geo import is_inside_comarapa
from core.pusher_service import notify_new_order

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Cart Views — available for anonymous and authenticated users
# ─────────────────────────────────────────────────────────────────────────────

def view_cart(request):
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
def add_to_cart(request, product_id):
    """Add a product to cart — works for anonymous and authenticated users, supports AJAX."""
    # Temporarily bypassed for testing
    request.session['location_valid'] = True
    if not request.session.get('location_valid', False):
        if not (request.user.is_authenticated and request.user.role in ['admin', 'agency']):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({"error": "No estás en la zona de entrega"}, status=403)
            return HttpResponseForbidden("No estás en la zona de entrega")

    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))

    if product.stock < quantity:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_ACCEPT') == 'application/json':
            return JsonResponse({"error": f"Lo sentimos, solo quedan {product.stock} unidades de {product.name}."}, status=400)
        messages.error(request, f"Lo sentimos, solo quedan {product.stock} unidades de {product.name}.")
        return redirect('landing')

    cart = _get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'price_at_time': product.price, 'price': product.price}
    )

    if not created:
        if cart_item.quantity + quantity > product.stock:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({"error": f"No puedes agregar más de {product.stock} unidades al carrito."}, status=400)
            messages.error(request, f"No puedes agregar más de {product.stock} unidades al carrito.")
            return redirect('view_cart')
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
        cart_item.price_at_time = product.price
        cart_item.price = product.price
    cart_item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_ACCEPT') == 'application/json' or request.POST.get('ajax') == '1':
        total_items = sum(item.quantity for item in cart.items.all())
        return JsonResponse({'total_items': total_items, 'success': True})

    messages.success(request, f"¡{product.name} agregado al carrito!")

    # After adding, redirect back to the landing page if not logged in
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '')
    if next_url:
        return redirect(next_url)
    return redirect('view_cart')


@require_POST
def update_cart_item(request, item_id):
    """Update quantity of a cart item."""
    cart = _get_or_create_cart(request)
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

    return redirect('view_cart')


@require_POST
def remove_cart_item(request, item_id):
    """Remove an item from the cart."""
    cart = _get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    name = cart_item.product.name
    cart_item.delete()
    messages.info(request, f"{name} eliminado del carrito.")
    return redirect('view_cart')


# Compatibility aliases
ver_carrito = view_cart
agregar_al_carrito = add_to_cart
actualizar_carrito = update_cart_item
eliminar_del_carrito = remove_cart_item


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

# ─────────────────────────────────────────────────────────────────────────────
# Checkout — 2-step flow with optional/forced login & registration
# ─────────────────────────────────────────────────────────────────────────────

def checkout_paso1(request):
    """Step 1: Collect shipping details, delivery instructions, and geolocate."""
    cart = _get_or_create_cart(request)
    if not cart.items.exists():
        messages.error(request, "Tu carrito está vacío.")
        return redirect('view_cart')

    coupon_id = request.session.get('applied_coupon_id')
    coupon = None
    discount = Decimal('0.00')
    if coupon_id and request.user.is_authenticated:
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
        instructions = request.POST.get('delivery_instructions', '').strip()
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')

        if not address:
            messages.error(request, "Por favor ingresa una dirección de entrega.")
            return render(request, 'client/checkout_paso1.html', {'cart': cart, 'total': total, 'coupon': coupon})

        if not lat or not lng:
            lat = "-17.920000"
            lng = "-64.530000"

        # TEMP: Geolocation check bypassed for testing
        # if not lat or not lng:
        #     messages.error(request, "Debes permitir la geolocalización o marcar tu ubicación en el mapa.")
        #     return render(request, 'client/checkout_paso1.html', {'cart': cart, 'total': total, 'coupon': coupon})

        # if not is_inside_comarapa(lat, lng):
        #     messages.error(request, "Error de Geolocalización: El servicio de entregas a domicilio solo está disponible dentro de Comarapa.")
        #     return render(request, 'client/checkout_paso1.html', {'cart': cart, 'total': total, 'coupon': coupon})

        # Save to session
        request.session['delivery_address'] = address
        request.session['delivery_instructions'] = instructions
        request.session['delivery_lat'] = str(lat)
        request.session['delivery_lng'] = str(lng)
        request.session['location_valid'] = True

        # Guest user details or authenticated user checkout
        if not request.user.is_authenticated:
            nombre_completo = request.POST.get('guest_name', '').strip()
            telefono = request.POST.get('guest_phone', '').strip()

            if not nombre_completo:
                messages.error(request, "Por favor ingresa tu nombre completo.")
                return render(request, 'client/checkout_paso1.html', {'cart': cart, 'total': total, 'coupon': coupon})
            if not telefono:
                messages.error(request, "Por favor ingresa tu número de celular.")
                return render(request, 'client/checkout_paso1.html', {'cart': cart, 'total': total, 'coupon': coupon})

            # Check if user already exists
            try:
                user = User.objects.get(telefono=telefono)
            except User.DoesNotExist:
                # Create a new user silently
                parts = nombre_completo.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
                import secrets
                random_pass = secrets.token_urlsafe(10)
                user = User.objects.create(
                    username=telefono,
                    telefono=telefono,
                    first_name=first_name,
                    last_name=last_name,
                    role=User.Roles.CLIENT,
                    address=address,
                    municipio="Comarapa"
                )
                user.set_password(random_pass)
                user.save()
                Cart.objects.get_or_create(user=user)

            # Silently login
            login(request, user, backend='accounts.backends.TelefonoBackend')
            transfer_cart(request, user)
            # Re-fetch the cart for the logged-in user to ensure we are ordering from the merged cart
            cart = _get_or_create_cart(request)

        # Now, create order for the (now authenticated) user
        try:
            with transaction.atomic():
                # Double check stock
                for item in cart.items.all():
                    if item.product.stock < item.quantity:
                        messages.error(request, f"Stock insuficiente para {item.product.name}. Solo quedan {item.product.stock} unidades.")
                        return redirect('view_cart')

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
                
                # Log state change
                OrderLog.objects.create(
                    order=order,
                    estado_anterior=None,
                    estado_nuevo=Order.Status.PENDING,
                    changed_by=request.user,
                    nota="Pedido creado por el cliente."
                )

                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        unit_price=item.price if item.price > 0 else item.price_at_time,
                    )
                    item.product.stock -= item.quantity
                    item.product.save()

                    InventoryLog.objects.create(
                        product=item.product,
                        user=request.user,
                        quantity=item.quantity,
                        movement_type=InventoryLog.MovementType.OUT,
                        reason=f"Descuento automático por pedido #{order.id}"
                    )

                if coupon:
                    coupon.used = True
                    coupon.save()
                    del request.session['applied_coupon_id']

                # Clear cart
                cart.items.all().delete()
                
                # Clean session keys
                request.session.pop('delivery_address', None)
                request.session.pop('delivery_instructions', None)
                request.session.pop('delivery_lat', None)
                request.session.pop('delivery_lng', None)

                # Pusher notification
                notify_new_order(order)
                
                # Simulate WhatsApp in console
                print(f"[SIMULACIÓN WHATSAPP] Notificación de nuevo pedido #{order.id} enviada al cliente {request.user.telefono}")

                messages.success(request, f"¡Pedido #{order.id} registrado exitosamente!")
                return redirect('client_ticket', order_id=order.id)
        except Exception as e:
            messages.error(request, f"Error al procesar el pedido: {str(e)}")
            return render(request, 'client/checkout_paso1.html', {'cart': cart, 'total': total, 'coupon': coupon})

    from django.conf import settings as django_settings
    # Default values for fields from session
    session_address = request.session.get('delivery_address', '')
    session_instructions = request.session.get('delivery_instructions', '')
    session_lat = request.session.get('delivery_lat', '')
    session_lng = request.session.get('delivery_lng', '')

    # If logged in, prefill user details
    if request.user.is_authenticated:
        if not session_address:
            session_address = request.user.address

    return render(request, 'client/checkout_paso1.html', {
        'cart': cart,
        'coupon': coupon,
        'discount': discount,
        'total': total,
        'google_maps_api_key': django_settings.GOOGLE_MAPS_API_KEY,
        'delivery_address': session_address,
        'delivery_instructions': session_instructions,
        'lat': session_lat,
        'lng': session_lng
    })


def checkout_paso2(request):
    """Step 2: Redundant, redirecting to one-step checkout."""
    return redirect('checkout')


@login_required
@role_required('client')
def client_ticket(request, order_id):
    """Confirm order success and show ticket."""
    order = get_object_or_404(Order, id=order_id, client=request.user)
    return render(request, 'client/ticket.html', {
        'order': order
    })


@csrf_exempt
def validate_location(request):
    """Ajax endpoint for validating location."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = data.get('lat')
            lng = data.get('lng')
            # TEMP: Force valid = True for testing
            valid = True
            
            # Save location validation in session
            request.session['location_valid'] = valid
            if valid:
                request.session['delivery_lat'] = str(lat) if lat else "-17.920000"
                request.session['delivery_lng'] = str(lng) if lng else "-64.530000"
            
            message = "Ubicación válida." if valid else "Ubicación fuera de la zona de entrega urbana de Comarapa."
            return JsonResponse({'valid': valid, 'message': message})
        except Exception as e:
            return JsonResponse({'valid': False, 'message': str(e)}, status=400)
    return JsonResponse({'valid': False, 'message': 'Método no permitido.'}, status=405)


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

