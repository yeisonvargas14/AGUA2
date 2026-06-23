import os
import secrets
from decimal import Decimal
from django import forms
from django.db.models import Sum
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
    driver_id = forms.ChoiceField(
        label="Repartidor",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_driver_id'})
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

        drivers = User.objects.filter(role=User.Roles.DRIVER, is_active=True).order_by('first_name', 'last_name')
        self.fields['driver_id'].choices = [('', '— Seleccionar repartidor —')] + [
            (d.id, f"{d.get_full_name() or d.username} ({d.telefono})") for d in drivers
        ]


@vendedor_required
def vendedor_dashboard(request):
    today = timezone.now().date()
    total_clients = User.objects.filter(role=User.Roles.CLIENT).count()
    clients_today = User.objects.filter(role=User.Roles.CLIENT, date_joined__date=today).count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    sales_today = Order.objects.filter(created_at__date=today).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()
    accepted_orders = Order.objects.filter(status=Order.Status.ACCEPTED).count()
    recent_orders = Order.objects.order_by('-created_at')[:6]

    return render(request, 'vendedor/dashboard.html', {
        'total_clients':  total_clients,
        'clients_today':  clients_today,
        'orders_today':   orders_today,
        'sales_today':    sales_today,
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
    date_filter = request.GET.get('date', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    orders = Order.objects.all().order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)

    if date_filter == 'today':
        today = timezone.now().date()
        orders = orders.filter(created_at__date=today)
    elif date_filter == 'week':
        today = timezone.now().date()
        week_start = today - timezone.timedelta(days=today.weekday())
        orders = orders.filter(created_at__date__gte=week_start)
    elif start_date and end_date:
        orders = orders.filter(created_at__date__range=[start_date, end_date])

    return render(request, 'vendedor/pedidos.html', {
        'orders': orders,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'start_date': start_date,
        'end_date': end_date,
    })


@vendedor_required
def vendedor_order_create(request):
    if request.method == 'POST':
        form = VendedorOrderForm(request.POST)
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')

        if form.is_valid() and product_ids:
            client_id = form.cleaned_data['client_id']
            client = get_object_or_404(User, pk=client_id, role=User.Roles.CLIENT)
            delivery_address = form.cleaned_data['delivery_address'] or client.address
            coupon_code = form.cleaned_data.get('coupon_code', '').strip()
            promotion_id = form.cleaned_data.get('promotion_id')
            driver_id = form.cleaned_data['driver_id']

            driver = get_object_or_404(User, pk=driver_id, role=User.Roles.DRIVER, is_active=True)

            coupon = None
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code, user_client=client, used=False)
                    if coupon.is_expired:
                        messages.error(request, f"El cupón '{coupon_code}' ha expirado.")
                        coupon = None
                except Coupon.DoesNotExist:
                    messages.error(request, f"El cupón '{coupon_code}' no existe o no pertenece a este cliente.")

            promotion = None
            if promotion_id:
                try:
                    now = timezone.now()
                    promotion = Promotion.objects.get(pk=promotion_id, is_active=True, start_date__lte=now, end_date__gte=now)
                except Promotion.DoesNotExist:
                    pass

            order = Order.objects.create(
                client=client,
                driver=driver,
                status=Order.Status.PENDING,
                delivery_address=delivery_address,
                coupon=coupon,
                total_amount=Decimal('0.00'),
                discount_amount=Decimal('0.00'),
            )

            total = Decimal('0.00')
            errors = []
            added_items = 0
            for pid, qty_str in zip(product_ids, quantities):
                try:
                    qty = max(1, int(qty_str))
                    product = Product.objects.get(pk=pid, is_active=True)
                    if product.stock < qty:
                        errors.append(f"Stock insuficiente para '{product.name}' (disponible: {product.stock}).")
                        continue

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
                    added_items += 1
                except (Product.DoesNotExist, ValueError):
                    continue

            if added_items == 0:
                order.delete()
                messages.error(request, "No se pudo crear el pedido. Verifica los productos agregados y el stock disponible.")
            else:
                discount_amount = Decimal('0.00')
                if coupon:
                    discount_amount = total * Decimal(str(coupon.discount_percentage)) / Decimal('100')
                    coupon.used = True
                    coupon.save()

                final_total = total - discount_amount
                order.total_amount = final_total
                order.discount_amount = discount_amount
                order.save()

                Delivery.objects.create(order=order, driver=driver)

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


@vendedor_required
def registrar_venta(request):
    from django.http import JsonResponse
    from django.db import transaction
    from django.db.models import Q
    import json

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos JSON inválidos.'}, status=400)

        client_id = data.get('client_id')
        metodo_pago = data.get('metodo_pago')
        items = data.get('items', [])

        if not client_id:
            return JsonResponse({'success': False, 'error': 'Debe seleccionar un cliente.'}, status=400)
        if not items:
            return JsonResponse({'success': False, 'error': 'Debe agregar al menos un producto.'}, status=400)

        client = get_object_or_404(User, pk=client_id, role=User.Roles.CLIENT)

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    client=client,
                    status=Order.Status.DELIVERED,
                    origen='venta_directa',
                    tipo_venta='presencial',
                    vendedor=request.user,
                    metodo_pago=metodo_pago,
                    delivery_address=client.address or 'Planta / Venta Presencial',
                    total_amount=Decimal('0.00'),
                )

                total = Decimal('0.00')
                for item in items:
                    pid = item.get('product_id')
                    qty = int(item.get('quantity', 0))
                    if qty <= 0:
                        continue

                    product = Product.objects.select_for_update().get(pk=pid, is_active=True)
                    if product.stock < qty:
                        raise ValueError(f"Stock insuficiente para '{product.name}' (Disponible: {product.stock})")

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        unit_price=product.price
                    )

                    product.stock -= qty
                    product.save()

                    InventoryLog.objects.create(
                        product=product,
                        user=request.user,
                        quantity=qty,
                        movement_type=InventoryLog.MovementType.OUT,
                        reason=f"Venta directa #{order.id} en planta"
                    )

                    total += product.price * qty

                if total == Decimal('0.00'):
                    raise ValueError("El total de la venta no puede ser 0.")

                order.total_amount = total
                order.save()

                OrderLog.objects.create(
                    order=order,
                    estado_anterior=None,
                    estado_nuevo=Order.Status.DELIVERED,
                    changed_by=request.user,
                    nota=f"Venta presencial registrada y entregada por vendedor {request.user.get_full_name() or request.user.username}"
                )

            return JsonResponse({'success': True, 'order_id': order.id, 'message': 'Venta registrada con éxito.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    # GET: render form and show latest 10 sales
    products = Product.objects.filter(is_active=True).order_by('name')
    
    # 10 recent delivered sales: registered by this vendedor or driver-delivered (vendedor is null/office)
    recent_sales = Order.objects.filter(
        status=Order.Status.DELIVERED
    ).filter(
        Q(vendedor=request.user) | Q(vendedor__isnull=True)
    ).order_by('-created_at')[:10]

    return render(request, 'vendedor/registrar_venta.html', {
        'products': products,
        'recent_sales': recent_sales,
    })


@vendedor_required
def buscar_clientes_venta(request):
    from django.http import JsonResponse
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'clients': []})

    clients = User.objects.filter(role=User.Roles.CLIENT).filter(
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q) |
        Q(telefono__icontains=q)
    )[:10]

    client_list = []
    for u in clients:
        client_list.append({
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'telefono': u.telefono or 'Sin celular',
            'address': u.address or ''
        })
    return JsonResponse({'clients': client_list})


@vendedor_required
def crear_cliente_rapido_venta(request):
    from django.http import JsonResponse
    import json
    import secrets

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos JSON inválidos.'}, status=400)

        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        telefono = data.get('telefono', '').strip()
        address = data.get('address', '').strip()

        if not first_name:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio.'}, status=400)
        if not telefono:
            return JsonResponse({'success': False, 'error': 'El celular es obligatorio.'}, status=400)

        # Check if username/phone already exists
        username = telefono
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Ya existe un usuario con este número de celular/usuario.'}, status=400)

        try:
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                telefono=telefono,
                address=address,
                role=User.Roles.CLIENT
            )
            user.set_password(User.objects.make_random_password())
            user.save()

            return JsonResponse({
                'success': True,
                'client': {
                    'id': user.id,
                    'name': user.get_full_name() or user.username,
                    'telefono': user.telefono,
                    'address': user.address
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


@vendedor_required
def vendedor_order_ticket(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'vendedor/ticket.html', {
        'order': order
    })


@vendedor_required
def ticket_venta(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'vendedor/ticket.html', {
        'order': order
    })


@vendedor_required
def listado_ventas(request):
    import csv
    from django.http import HttpResponse
    from django.db.models import Q
    from django.utils.timezone import make_aware
    from datetime import datetime

    # Get query parameters
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    metodo_pago = request.GET.get('metodo_pago', '')
    tipo_venta_filter = request.GET.get('tipo_venta', '')

    # Base query: delivered online orders OR any direct presencial sale
    orders = Order.objects.filter(
        Q(tipo_venta='presencial') | Q(tipo_venta='online', status=Order.Status.DELIVERED)
    ).order_by('-created_at')

    # Apply filters
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            orders = orders.filter(created_at__date__gte=start_date.date())
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            orders = orders.filter(created_at__date__lte=end_date.date())
        except ValueError:
            pass

    if metodo_pago:
        orders = orders.filter(metodo_pago=metodo_pago)

    if tipo_venta_filter:
        orders = orders.filter(tipo_venta=tipo_venta_filter)

    # Export to CSV option
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="planilla_ventas.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID Venta', 'Tipo de Venta', 'Cliente', 'Celular', 'Fecha', 'Método Pago', 'Estado', 'Total (Bs)'])
        
        for o in orders:
            writer.writerow([
                o.id,
                o.get_tipo_venta_display() if hasattr(o, 'get_tipo_venta_display') else o.tipo_venta,
                o.client.get_full_name() or o.client.username,
                o.client.telefono or '—',
                o.created_at.strftime('%d/%m/%Y %H:%M'),
                o.get_metodo_pago_display() or '—',
                o.get_status_display(),
                o.total_amount
            ])
        return response

    return render(request, 'vendedor/listado_ventas.html', {
        'orders': orders,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'metodo_pago': metodo_pago,
        'tipo_venta': tipo_venta_filter,
    })

