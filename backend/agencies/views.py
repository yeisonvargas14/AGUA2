from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal

from orders.models import Order, OrderItem
from products.models import Product
from inventory.models import InventoryLog
from .models import Agency
from .decorators import agency_active_required


# -----------------------------------------------------------------
# Agency Dashboard
# -----------------------------------------------------------------
@agency_active_required
def agency_dashboard(request):
    agency = request.user.agencia
    status_filter = request.GET.get('status', '')
    orders = Order.objects.filter(agency=agency).order_by('-created_at')

    if status_filter:
        orders = orders.filter(status=status_filter)

    delivered_orders = Order.objects.filter(agency=agency, status=Order.Status.DELIVERED)
    total_sales = delivered_orders.aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')
    total_orders = Order.objects.filter(agency=agency).count()
    pending_count = Order.objects.filter(agency=agency, status=Order.Status.PENDING).count()

    return render(request, 'agency/dashboard.html', {
        'agency': agency,
        'orders': orders,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'pending_count': pending_count,
        'status_filter': status_filter,
        'status_choices': Order.Status.choices,
    })


# -----------------------------------------------------------------
# Create Order (from Agency)
# -----------------------------------------------------------------
@agency_active_required
def agency_create_order(request):
    agency = request.user.agencia
    products = Product.objects.filter(is_active=True)

    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 1))
        client_name = request.POST.get('client_name', '').strip()
        address = request.POST.get('address', '').strip()

        product = get_object_or_404(Product, id=product_id, is_active=True)

        if product.stock < quantity:
            messages.error(request, f"Stock insuficiente para {product.name}. Solo hay {product.stock} disponibles.")
            return render(request, 'agency/crear_pedido.html', {'products': products})

        if not address:
            messages.error(request, "Por favor ingresa la dirección de entrega.")
            return render(request, 'agency/crear_pedido.html', {'products': products})

        order = Order.objects.create(
            client=request.user,
            agency=agency,
            total_amount=product.price * quantity,
            delivery_address=f"[AGENCIA] {client_name} — {address}",
            status=Order.Status.PENDING
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.price
        )

        product.stock -= quantity
        product.save()

        InventoryLog.objects.create(
            product=product,
            user=request.user,
            quantity=quantity,
            movement_type=InventoryLog.MovementType.OUT,
            reason=f"Venta registrada por agencia '{agency.nombre_empresa}'"
        )

        messages.success(request, f"Pedido #{order.id} registrado con éxito en {agency.nombre_empresa}.")
        return redirect('agency_dashboard')

    return render(request, 'agency/crear_pedido.html', {'products': products})


# -----------------------------------------------------------------
# Agency Change Password
# -----------------------------------------------------------------
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
