from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal

from core.decorators import role_required
from products.models import Product
from orders.models import Order, OrderItem
from inventory.models import InventoryLog
from .models import Agency

@login_required
@role_required('agency')
def agency_dashboard(request):
    try:
        agency = request.user.managed_agency
    except Agency.DoesNotExist:
        agency = None

    orders = []
    total_sales = Decimal('0.00')
    if agency:
        orders = Order.objects.filter(agency=agency).order_by('-created_at')
        delivered_orders = orders.filter(status=Order.Status.DELIVERED)
        total_sales = sum(o.total_amount for o in delivered_orders)

    return render(request, 'agency/dashboard.html', {
        'agency': agency,
        'orders': orders,
        'total_sales': total_sales
    })

@login_required
@role_required('agency')
def agency_create_order(request):
    try:
        agency = request.user.managed_agency
    except Agency.DoesNotExist:
        messages.error(request, "No tienes una agencia asignada. Contacta al administrador.")
        return redirect('agency_dashboard')

    products = Product.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Simple manual order creation by Agency
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

        # For Agency orders, since there is no standard client registered in auth sometimes, 
        # we can assign it to the agency manager or have a standard dummy client. Let's assign to the agency manager as client.
        # This keeps the DB relationships clean!
        order = Order.objects.create(
            client=request.user, # Agency user acts as client for tracking
            agency=agency,
            total_amount=product.price * quantity,
            delivery_address=f"[AGENCIA] {client_name} - {address}",
            status=Order.Status.PENDING
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.price
        )

        # Deduct stock
        product.stock -= quantity
        product.save()

        # Log inventory movement
        InventoryLog.objects.create(
            product=product,
            user=request.user,
            quantity=quantity,
            movement_type=InventoryLog.MovementType.OUT,
            reason=f"Pedido registrado en agencia por {request.user.username}"
        )

        messages.success(request, f"Pedido #{order.id} registrado con éxito en {agency.name}.")
        return redirect('agency_dashboard')

    return render(request, 'agency/crear_pedido.html', {
        'products': products
    })
