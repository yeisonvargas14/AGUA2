from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Sum
from decimal import Decimal
import datetime

from orders.models import Order, OrderItem, AgencyCart, AgencyCartItem
from products.models import Product
from .decorators import agency_active_required


@agency_active_required
def agency_dashboard(request):
    agency = request.user.agencia
    orders = Order.objects.filter(agency=agency).order_by('-created_at')
    
    total_orders = orders.count()
    last_order = orders.first()
    
    # Próxima entrega: el pedido con fecha de entrega deseada >= hoy, más cercano
    proxima_entrega = orders.filter(
        fecha_entrega_deseada__gte=timezone.now().date(),
        status__in=[Order.Status.PENDING, Order.Status.ACCEPTED, Order.Status.ON_WAY]
    ).order_by('fecha_entrega_deseada').first()

    return render(request, 'agency/dashboard.html', {
        'agency': agency,
        'total_orders': total_orders,
        'last_order': last_order,
        'proxima_entrega': proxima_entrega,
    })


@agency_active_required
def agency_catalog(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'agency/catalog.html', {
        'products': products
    })


@agency_active_required
def agency_add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        quantity = int(request.POST.get('quantity', 1))

        if quantity <= 0:
            messages.error(request, "La cantidad debe ser mayor a 0.")
            return redirect('agency_catalog')

        if product.stock < quantity:
            messages.error(request, f"Stock insuficiente. Solo hay {product.stock} disponibles.")
            return redirect('agency_catalog')

        agency = request.user.agencia
        cart, created = AgencyCart.objects.get_or_create(agency=agency)

        cart_item, item_created = AgencyCartItem.objects.get_or_create(
            cart=cart, 
            product=product,
            defaults={'price': product.get_agency_price, 'quantity': quantity}
        )

        if not item_created:
            new_quantity = cart_item.quantity + quantity
            if product.stock < new_quantity:
                messages.error(request, f"Stock insuficiente al sumar a tu carrito. Tienes {cart_item.quantity} y hay {product.stock} disponibles.")
                return redirect('agency_catalog')
            cart_item.quantity = new_quantity
            cart_item.save()

        messages.success(request, f"{product.name} agregado al carrito.")
        return redirect('agency_catalog')
    return redirect('agency_catalog')


@agency_active_required
def agency_cart(request):
    agency = request.user.agencia
    cart = AgencyCart.objects.filter(agency=agency).first()
    
    if request.method == 'POST':
        item_id = request.POST.get('remove_item')
        if item_id and cart:
            AgencyCartItem.objects.filter(id=item_id, cart=cart).delete()
            messages.success(request, "Producto eliminado del carrito.")
            return redirect('agency_cart')

    return render(request, 'agency/cart.html', {
        'cart': cart
    })


@agency_active_required
def agency_checkout(request):
    agency = request.user.agencia
    cart = AgencyCart.objects.filter(agency=agency).first()

    if not cart or cart.items.count() == 0:
        messages.error(request, "Tu carrito está vacío.")
        return redirect('agency_catalog')

    if request.method == 'POST':
        fecha_str = request.POST.get('fecha_entrega_deseada')
        
        if not fecha_str:
            messages.error(request, "Debes seleccionar una fecha de entrega.")
            return render(request, 'agency/checkout.html', {'cart': cart})

        try:
            fecha_entrega = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Formato de fecha inválido.")
            return render(request, 'agency/checkout.html', {'cart': cart})

        ahora = timezone.now()
        # Mínimo 24 horas: la fecha deseada debe ser > fecha_actual + 1 día
        min_date = ahora.date() + datetime.timedelta(days=1)
        
        if fecha_entrega < min_date:
            messages.error(request, "La fecha de entrega debe tener al menos 24 horas de anticipación.")
            return render(request, 'agency/checkout.html', {'cart': cart})

        # Validar stock nuevamente
        for item in cart.items.all():
            if item.product.stock < item.quantity:
                messages.error(request, f"Stock insuficiente para {item.product.name} durante el checkout.")
                return redirect('agency_cart')

        # Crear Order
        total = cart.total_amount
        order = Order.objects.create(
            client=request.user, # The agency manager is the client here
            agency=agency,
            total_amount=total,
            fecha_entrega_deseada=fecha_entrega,
            tipo_pedido='agencia',
            status=Order.Status.PENDING,
            delivery_address=agency.direccion
        )

        # Crear OrderItems y descontar stock
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.price
            )
            item.product.stock -= item.quantity
            item.product.save()

        # Vaciar carrito
        cart.delete()

        messages.success(request, "Pedido confirmado con éxito.")
        return redirect('agency_ticket', order_id=order.id)

    return render(request, 'agency/checkout.html', {
        'cart': cart,
        'min_date': (timezone.now().date() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    })


@agency_active_required
def agency_ticket(request, order_id):
    agency = request.user.agencia
    order = get_object_or_404(Order, id=order_id, agency=agency)
    return render(request, 'agency/ticket.html', {
        'order': order,
        'agency': agency
    })


@agency_active_required
def agency_orders(request):
    agency = request.user.agencia
    orders = Order.objects.filter(agency=agency).order_by('-created_at')
    return render(request, 'agency/orders.html', {
        'orders': orders
    })


@agency_active_required
def agency_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Contraseña cambiada con éxito.")
            return redirect('agency_dashboard')
        else:
            messages.error(request, "Por favor corrige los errores indicados.")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'agency/cambiar_contrasena.html', {'form': form})

