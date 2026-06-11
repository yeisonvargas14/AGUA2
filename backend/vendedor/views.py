import os
import secrets
from decimal import Decimal
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone

from accounts.models import User, DriverProfile
from agencies.models import Agency
from products.models import Product
from orders.models import Order, OrderItem, OrderLog
from coupons.models import Coupon
from promotions.models import Promotion
from inventory.models import InventoryLog
from distribution.models import Delivery

# Decorator to restrict access only to users with role 'vendedor'
vendedor_required = user_passes_test(
    lambda u: u.is_authenticated and u.role == User.Roles.VENDEDOR,
    login_url='login'
)


class ClienteRapidoForm(forms.ModelForm):
    """Form to create or edit a client quickly from the seller panel."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 6 caracteres'}),
        required=False,
        help_text="Dejar en blanco al editar para mantener la contraseña actual."
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'telefono', 'address', 'municipio']
        widgets = {
            'first_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan'}),
            'last_name':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez'}),
            'telefono':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 70123456'}),
            'address':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección de entrega'}),
            'municipio':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Comarapa'}),
        }


class VendedorOrderForm(forms.Form):
    """Form for the seller to create an order on behalf of a client."""
    client_id = forms.ChoiceField(
        label="Cliente",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_client_id'})
    )
    delivery_address = forms.CharField(
        label="Dirección de entrega",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Calle Bolívar #45'}),
        required=False
    )
    coupon_code = forms.CharField(
        label="Código de cupón (opcional)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: DESCUENTO15'})
    )
    promotion_id = forms.ChoiceField(
        label="Promoción activa (opcional)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        clients = User.objects.filter(role=User.Roles.CLIENT).order_by('first_name')
        self.fields['client_id'].choices = [('', '— Seleccionar cliente —')] + [
            (u.id, f"{u.get_full_name() or u.username} ({u.telefono or 'Sin celular'})") for u in clients
        ]
        now = timezone.now()
        active_promos = Promotion.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)
        self.fields['promotion_id'].choices = [('', '— Sin promoción —')] + [
            (p.id, f"{p.name} ({p.discount_percentage}%)") for p in active_promos
        ]


@vendedor_required
def vendedor_dashboard(request):
    today = timezone.now().date()
    total_clients = User.objects.filter(role=User.Roles.CLIENT).count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()
    accepted_orders = Order.objects.filter(status=Order.Status.ACCEPTED).count()
    recent_orders = Order.objects.order_by('-created_at')[:6]

    return render(request, 'vendedor/dashboard.html', {
        'total_clients':  total_clients,
        'orders_today':   orders_today,
        'pending_orders': pending_orders,
        'accepted_orders': accepted_orders,
        'recent_orders':  recent_orders,
    })


@vendedor_required
def vendedor_clients(request):
    q = request.GET.get('q', '')
    clients = User.objects.filter(role=User.Roles.CLIENT).order_by('-date_joined')
    if q:
        clients = clients.filter(
            first_name__icontains=q
        ) | clients.filter(
            last_name__icontains=q
        ) | clients.filter(
            telefono__icontains=q
        )
    return render(request, 'vendedor/clientes.html', {'clients': clients, 'q': q})


@vendedor_required
def vendedor_client_create(request):
    if request.method == 'POST':
        form = ClienteRapidoForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Roles.CLIENT
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            else:
                user.set_password(User.objects.make_random_password())
            
            # Auto-generate a username if not provided
            if not user.username:
                user.username = user.telefono or f"client_{secrets.token_hex(4)}"
            user.save()
            messages.success(request, f"Cliente '{user.get_full_name() or user.telefono}' registrado exitosamente.")
            return redirect('vendedor_clients')
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = ClienteRapidoForm()
    return render(request, 'vendedor/cliente_form.html', {'form': form, 'title': 'Registrar Nuevo Cliente', 'is_create': True})


@vendedor_required
def vendedor_client_edit(request, pk):
    client = get_object_or_404(User, pk=pk, role=User.Roles.CLIENT)
    if request.method == 'POST':
        form = ClienteRapidoForm(request.POST, instance=client)
        if form.is_valid():
            u = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                u.set_password(password)
            u.save()
            messages.success(request, f"Cliente '{u.get_full_name() or u.telefono}' actualizado exitosamente.")
            return redirect('vendedor_clients')
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = ClienteRapidoForm(instance=client)
    return render(request, 'vendedor/cliente_form.html', {'form': form, 'title': 'Editar Cliente', 'client': client, 'is_create': False})


@vendedor_required
def vendedor_orders(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all().order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'vendedor/pedidos.html', {
        'orders': orders,
        'status_filter': status_filter,
    })


@vendedor_required
def vendedor_order_create(request):
    if request.method == 'POST':
        form = VendedorOrderForm(request.POST)
        # Collect product lines from POST
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')

        if form.is_valid() and product_ids:
            client_id = form.cleaned_data['client_id']
            client = get_object_or_404(User, pk=client_id, role=User.Roles.CLIENT)
            delivery_address = form.cleaned_data['delivery_address'] or client.address
            coupon_code = form.cleaned_data.get('coupon_code', '').strip()
            promotion_id = form.cleaned_data.get('promotion_id')

            # Validate coupon
            coupon = None
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code, user_client=client, used=False)
                    if coupon.is_expired:
                        messages.error(request, f"El cupón '{coupon_code}' ha expirado.")
                        coupon = None
                except Coupon.DoesNotExist:
                    messages.error(request, f"El cupón '{coupon_code}' no existe o no pertenece a este cliente.")

            # Validate promotion
            promotion = None
            if promotion_id:
                try:
                    now = timezone.now()
                    promotion = Promotion.objects.get(pk=promotion_id, is_active=True, start_date__lte=now, end_date__gte=now)
                except Promotion.DoesNotExist:
                    pass

            # Build order
            order = Order.objects.create(
                client=client,
                status=Order.Status.PENDING,
                delivery_address=delivery_address,
                coupon=coupon,
                total_amount=Decimal('0.00'),
                discount_amount=Decimal('0.00'),
            )

            total = Decimal('0.00')
            errors = []
            for pid, qty_str in zip(product_ids, quantities):
                try:
                    qty = max(1, int(qty_str))
                    product = Product.objects.get(pk=pid, is_active=True)
                    if product.stock < qty:
                        errors.append(f"Stock insuficiente para '{product.name}' (disponible: {product.stock}).")
                        continue
                    # Apply promotion discount if product is in promotion
                    unit_price = product.price
                    if promotion and promotion.products.filter(pk=product.pk).exists():
                        discount = product.price * Decimal(str(promotion.discount_percentage)) / Decimal('100')
                        unit_price = product.price - discount

                    OrderItem.objects.create(order=order, product=product, quantity=qty, unit_price=unit_price)
                    product.stock -= qty
                    product.save()
                    InventoryLog.objects.create(
                        product=product, user=request.user, quantity=qty,
                        movement_type=InventoryLog.MovementType.OUT,
                        reason=f"Pedido #{order.id} registrado por Vendedor"
                    )
                    total += unit_price * qty
                except (Product.DoesNotExist, ValueError):
                    continue

            # Apply coupon discount
            discount_amount = Decimal('0.00')
            if coupon:
                discount_amount = total * Decimal(str(coupon.discount_percentage)) / Decimal('100')
                coupon.used = True
                coupon.save()

            order.total_amount = total
            order.discount_amount = discount_amount
            order.save()

            # Log creation
            OrderLog.objects.create(
                order=order,
                estado_anterior=None,
                estado_nuevo=Order.Status.PENDING,
                changed_by=request.user,
                nota=f"Pedido creado por Vendedor: {request.user.get_full_name() or request.user.username}"
            )

            for err in errors:
                messages.warning(request, err)

            messages.success(request, f"Pedido #{order.id} creado exitosamente para {client.get_full_name() or client.telefono}.")
            return redirect('vendedor_order_detail', pk=order.id)
        else:
            if not product_ids:
                messages.error(request, "Debes agregar al menos un producto al pedido.")

    else:
        form = VendedorOrderForm()

    products = Product.objects.filter(is_active=True).order_by('name')
    return render(request, 'vendedor/pedido_nuevo.html', {'form': form, 'products': products})


@vendedor_required
def vendedor_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    drivers = User.objects.filter(role=User.Roles.DRIVER, is_active=True)
    can_cancel = order.status == Order.Status.PENDING
    can_assign = order.status in [Order.Status.PENDING, Order.Status.ACCEPTED]
    return render(request, 'vendedor/pedido_detalle.html', {
        'order': order,
        'drivers': drivers,
        'can_cancel': can_cancel,
        'can_assign': can_assign,
    })


@vendedor_required
def vendedor_order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status != Order.Status.PENDING:
        messages.error(request, "Solo puedes cancelar pedidos en estado Pendiente.")
        return redirect('vendedor_order_detail', pk=order.id)

    if request.method == 'POST':
        old_status = order.status
        # Restore stock
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()
            InventoryLog.objects.create(
                product=item.product, user=request.user, quantity=item.quantity,
                movement_type=InventoryLog.MovementType.IN,
                reason=f"Restauración de stock por cancelación del Pedido #{order.id}"
            )
        order.status = Order.Status.CANCELLED
        order.save()
        OrderLog.objects.create(
            order=order, estado_anterior=old_status, estado_nuevo=Order.Status.CANCELLED,
            changed_by=request.user,
            nota="Pedido cancelado por Vendedor."
        )
        messages.success(request, f"Pedido #{order.id} cancelado y stock restaurado.")
        return redirect('vendedor_orders')

    return render(request, 'vendedor/pedido_cancelar.html', {'order': order})


@vendedor_required
def vendedor_assign_driver(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status not in [Order.Status.PENDING, Order.Status.ACCEPTED]:
        messages.error(request, "No puedes reasignar un pedido que ya está en camino o entregado.")
        return redirect('vendedor_order_detail', pk=order.id)

    if request.method == 'POST':
        driver_id = request.POST.get('driver')
        driver = get_object_or_404(User, id=driver_id, role=User.Roles.DRIVER)
        old_status = order.status
        order.driver = driver
        order.status = Order.Status.ACCEPTED
        order.save()
        Delivery.objects.update_or_create(order=order, defaults={'driver': driver})
        OrderLog.objects.create(
            order=order, estado_anterior=old_status, estado_nuevo=Order.Status.ACCEPTED,
            changed_by=request.user,
            nota=f"Pedido asignado al repartidor '{driver.get_full_name() or driver.username}' por Vendedor."
        )
        messages.success(request, f"Pedido #{order.id} asignado a {driver.get_full_name() or driver.username}.")

    return redirect('vendedor_order_detail', pk=order.id)


@vendedor_required
def vendedor_catalog(request):
    q = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True).order_by('name')
    if q:
        products = products.filter(name__icontains=q)
    return render(request, 'vendedor/catalogo.html', {'products': products, 'q': q})
