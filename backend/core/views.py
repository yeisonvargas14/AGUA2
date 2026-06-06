from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from decimal import Decimal
from django import forms

from core.decorators import role_required
from accounts.models import User
from products.models import Product
from orders.models import Order, OrderItem
from coupons.models import Coupon
from promotions.models import Promotion
from ratings.models import Rating
from inventory.models import InventoryLog
from distribution.models import Delivery
from agencies.models import Agency

# =====================================================================
# ADMIN DASHBOARD
# =====================================================================
@login_required
@role_required('admin')
def admin_dashboard(request):
    today = timezone.now().date()
    
    # Metrics calculations
    total_sales = Order.objects.filter(status=Order.Status.DELIVERED).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_orders = Order.objects.count()
    active_deliveries = Order.objects.filter(status__in=[Order.Status.ACCEPTED, Order.Status.ON_WAY]).count()
    low_stock = Product.objects.filter(stock__lte=15).count()
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:8]
    
    # Low stock items
    stock_alerts = Product.objects.filter(stock__lte=20).order_by('stock')[:5]

    return render(request, 'admin_panel/dashboard.html', {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'active_deliveries': active_deliveries,
        'low_stock': low_stock,
        'recent_orders': recent_orders,
        'stock_alerts': stock_alerts
    })

# =====================================================================
# PRODUCTS CRUD
# =====================================================================
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

@login_required
@role_required('admin')
def admin_products(request):
    products = Product.objects.all().order_by('id')
    return render(request, 'admin_panel/productos.html', {'products': products})

@login_required
@role_required('admin')
def admin_product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            
            # Log initial inventory
            if product.stock > 0:
                InventoryLog.objects.create(
                    product=product,
                    user=request.user,
                    quantity=product.stock,
                    movement_type=InventoryLog.MovementType.IN,
                    reason="Stock inicial al registrar producto"
                )
            
            messages.success(request, f"Producto '{product.name}' registrado con éxito.")
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(request, 'admin_panel/producto_form.html', {'form': form, 'title': 'Registrar Nuevo Producto'})

@login_required
@role_required('admin')
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    old_stock = product.stock
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            
            # Log inventory difference if stock is adjusted
            if product.stock != old_stock:
                diff = product.stock - old_stock
                mov_type = InventoryLog.MovementType.IN if diff > 0 else InventoryLog.MovementType.OUT
                InventoryLog.objects.create(
                    product=product,
                    user=request.user,
                    quantity=abs(diff),
                    movement_type=mov_type,
                    reason="Ajuste manual de stock por el Administrador"
                )
                
            messages.success(request, f"Producto '{product.name}' actualizado con éxito.")
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_panel/producto_form.html', {'form': form, 'title': 'Editar Producto'})

@login_required
@role_required('admin')
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, "Producto eliminado exitosamente.")
    return redirect('admin_products')

# =====================================================================
# USERS CRUD
# =====================================================================
class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False, help_text="Dejar en blanco para mantener la actual.")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'address', 'municipio']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'municipio': forms.TextInput(attrs={'class': 'form-control'}),
        }

@login_required
@role_required('admin')
def admin_users(request):
    users = User.objects.all().order_by('id')
    return render(request, 'admin_panel/usuarios.html', {'users': users})

@login_required
@role_required('admin')
def admin_user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            messages.success(request, f"Usuario '{user.username}' creado exitosamente.")
            return redirect('admin_users')
    else:
        form = UserForm()
    return render(request, 'admin_panel/usuario_form.html', {'form': form, 'title': 'Registrar Nuevo Usuario'})

@login_required
@role_required('admin')
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            u = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                u.set_password(password)
            u.save()
            messages.success(request, f"Usuario '{u.username}' actualizado exitosamente.")
            return redirect('admin_users')
    else:
        form = UserForm(instance=user)
    return render(request, 'admin_panel/usuario_form.html', {'form': form, 'title': 'Editar Usuario'})

@login_required
@role_required('admin')
def admin_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    messages.success(request, "Usuario eliminado con éxito.")
    return redirect('admin_users')

# =====================================================================
# COUPONS CRUD
# =====================================================================
class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'user_client', 'discount_percentage', 'expires_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EJ: DESCUENTO15'}),
            'user_client': forms.Select(attrs={'class': 'form-control'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

@login_required
@role_required('admin')
def admin_coupons(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/cupones.html', {'coupons': coupons})

@login_required
@role_required('admin')
def admin_coupon_create(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save()
            messages.success(request, f"Cupón '{coupon.code}' creado con éxito.")
            return redirect('admin_coupons')
    else:
        form = CouponForm()
    return render(request, 'admin_panel/cupon_form.html', {'form': form})

@login_required
@role_required('admin')
def admin_coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.delete()
    messages.success(request, "Cupón eliminado exitosamente.")
    return redirect('admin_coupons')

# =====================================================================
# PROMOTIONS CRUD
# =====================================================================
class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['name', 'description', 'discount_percentage', 'products', 'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'products': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

@login_required
@role_required('admin')
def admin_promotions(request):
    promotions = Promotion.objects.all().order_by('-id')
    return render(request, 'admin_panel/promociones.html', {'promotions': promotions})

@login_required
@role_required('admin')
def admin_promotion_create(request):
    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            promo = form.save()
            messages.success(request, f"Promoción '{promo.name}' creada con éxito.")
            return redirect('admin_promotions')
    else:
        form = PromotionForm()
    return render(request, 'admin_panel/promocion_form.html', {'form': form})

@login_required
@role_required('admin')
def admin_promotion_delete(request, pk):
    promo = get_object_or_404(Promotion, pk=pk)
    promo.delete()
    messages.success(request, "Promoción eliminada exitosamente.")
    return redirect('admin_promotions')

# =====================================================================
# ORDERS MANAGEMENT & DRIVER ASSIGNMENT
# =====================================================================
@login_required
@role_required('admin')
def admin_orders(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all().order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    return render(request, 'admin_panel/pedidos.html', {
        'orders': orders,
        'status_filter': status_filter
    })

@login_required
@role_required('admin')
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    drivers = User.objects.filter(role=User.Roles.DRIVER)
    return render(request, 'admin_panel/pedido_detalle.html', {
        'order': order,
        'drivers': drivers
    })

@login_required
@role_required('admin')
def admin_assign_driver(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        driver_id = request.POST.get('driver')
        driver = get_object_or_404(User, id=driver_id, role=User.Roles.DRIVER)
        
        order.driver = driver
        order.status = Order.Status.ACCEPTED
        order.save()
        
        # Create or update Delivery log
        Delivery.objects.update_or_create(
            order=order,
            defaults={'driver': driver}
        )
        
        messages.success(request, f"Pedido #{order.id} asignado al repartidor '{driver.get_full_name() or driver.username}'.")
    return redirect('admin_order_detail', pk=order.id)

# =====================================================================
# REPORTS
# =====================================================================
@login_required
@role_required('admin')
def admin_reports(request):
    # Sales by day (last 15 days)
    sales_by_day = Order.objects.filter(
        status=Order.Status.DELIVERED,
        created_at__gte=timezone.now() - timezone.timedelta(days=15)
    ).annotate(date=TruncDate('created_at')).values('date').annotate(total=Sum('total_amount')).order_by('date')
    
    # Top selling products
    top_products = OrderItem.objects.filter(
        order__status=Order.Status.DELIVERED
    ).values('product__name').annotate(sold_qty=Sum('quantity'), sales=Sum('unit_price')).order_by('-sold_qty')[:5]
    
    # Delivery performance ratings
    driver_ratings = Rating.objects.filter(driver__isnull=False).values('driver__username').annotate(
        avg_score=Avg('score'), count=Count('id')
    ).order_by('-avg_score')

    return render(request, 'admin_panel/reportes.html', {
        'sales_by_day': sales_by_day,
        'top_products': top_products,
        'driver_ratings': driver_ratings
    })

# =====================================================================
# API ENDPOINTS (REST SPA Dashboard)
# =====================================================================

@csrf_exempt
def seed_data(request):
    """Seeds sample data into the database if empty to make the dashboard beautiful immediately."""
    try:
        # Ensure at least one user exists
        user = User.objects.first()
        if not user:
            user = User.objects.create_superuser(
                username='yeison',
                email='yeison@example.com',
                password='adminpassword',
                role=User.Roles.ADMIN
            )
        
        # Seed Products
        if Product.objects.count() == 0:
            p1 = Product.objects.create(name="Bidón de Agua 20L", description="Agua purificada en presentación de bidón retornable.", price=Decimal("12.00"), stock=15)
            p2 = Product.objects.create(name="Botella Personal 500ml", description="Pack de 6 botellas de agua purificada de 500ml.", price=Decimal("15.00"), stock=350)
            p3 = Product.objects.create(name="Dispensor de Agua de Mesa", description="Dispensor mecánico para bidones de agua.", price=Decimal("45.00"), stock=5)
            p4 = Product.objects.create(name="Bidón de Agua 10L", description="Bidón mediano de agua purificada.", price=Decimal("7.00"), stock=60)
        else:
            p1, p2, p3 = Product.objects.all()[:3]
            p4 = Product.objects.all()[3] if Product.objects.count() > 3 else p1

        # Seed Agencies
        if Agency.objects.count() == 0:
            # Create agency managers if they don't exist
            manager1, _ = User.objects.get_or_create(username='agente1', defaults={'role': User.Roles.AGENCY, 'email': 'agente1@example.com'})
            manager2, _ = User.objects.get_or_create(username='agente2', defaults={'role': User.Roles.AGENCY, 'email': 'agente2@example.com'})
            Agency.objects.create(name="Agencia Zona Norte - Comarapa", address="Av. Libertadores #45", manager=manager1)
            Agency.objects.create(name="Agencia Central", address="Calle Bolivar #120", manager=manager2)

        # Seed Orders
        if Order.objects.count() == 0:
            # Create driver
            driver, _ = User.objects.get_or_create(username='repartidor1', defaults={'role': User.Roles.DRIVER, 'email': 'rep1@example.com'})
            
            # Order 1 (Delivered)
            o1 = Order.objects.create(client=user, status=Order.Status.DELIVERED, total_amount=Decimal("120.00"), delivery_address="Calle Florida #10")
            OrderItem.objects.create(order=o1, product=p1, quantity=10, unit_price=Decimal("12.00"))
            Delivery.objects.create(order=o1, driver=driver, notes="Entregado a tiempo. Todo conforme.", delivered_at=o1.created_at)

            # Order 2 (Shipped)
            o2 = Order.objects.create(client=user, status=Order.Status.ON_WAY, total_amount=Decimal("45.00"), delivery_address="Av. Aroma #200")
            OrderItem.objects.create(order=o2, product=p3, quantity=1, unit_price=Decimal("45.00"))
            Delivery.objects.create(order=o2, driver=driver, notes="En ruta de distribución.")

            # Order 3 (Preparing)
            o3 = Order.objects.create(client=user, status=Order.Status.ACCEPTED, total_amount=Decimal("210.00"), delivery_address="Agencia Norte")
            OrderItem.objects.create(order=o3, product=p2, quantity=14, unit_price=Decimal("15.00"))

        return JsonResponse({"status": "success", "message": "Datos de prueba creados exitosamente."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def api_dashboard_stats(request):
    """Returns dashboard numeric statistics."""
    try:
        # Run seed automatically if empty
        if Product.objects.count() == 0:
            try:
                seed_data(request)
            except Exception:
                pass

        total_products = Product.objects.count()
        total_orders = Order.objects.count()
        active_deliveries = Order.objects.filter(status__in=[Order.Status.PENDING, Order.Status.ACCEPTED, Order.Status.ON_WAY]).count()
        
        # Calculate monthly income (sum of all delivered orders)
        income = sum(o.total_amount for o in Order.objects.filter(status=Order.Status.DELIVERED))
        
        # Low stock alerts count
        low_stock_count = Product.objects.filter(stock__lte=20).count()

        return JsonResponse({
            "products_count": total_products,
            "orders_count": total_orders,
            "active_deliveries": active_deliveries,
            "monthly_income": float(income),
            "low_stock_count": low_stock_count
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def api_products(request):
    """API for managing products."""
    try:
        if request.method == 'GET':
            products = Product.objects.all().order_by('id')
            data = []
            for p in products:
                data.append({
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": float(p.price),
                    "stock": p.stock,
                    "is_active": p.is_active
                })
            return JsonResponse(data, safe=False)

        elif request.method == 'POST':
            body = json.loads(request.body)
            p = Product.objects.create(
                name=body['name'],
                description=body.get('description', ''),
                price=Decimal(str(body['price'])),
                stock=int(body.get('stock', 0))
            )
            # Log initial stock movement if > 0
            if p.stock > 0:
                user = User.objects.first()
                InventoryLog.objects.create(
                    product=p,
                    user=user,
                    quantity=p.stock,
                    movement_type=InventoryLog.MovementType.IN,
                    reason="Stock inicial al crear producto"
                )
            return JsonResponse({"status": "success", "id": p.id})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def api_product_detail(request, pk):
    """API to edit or delete a specific product."""
    try:
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Producto no encontrado"}, status=404)

        if request.method == 'PUT':
            body = json.loads(request.body)
            product.name = body.get('name', product.name)
            product.description = body.get('description', product.description)
            product.price = Decimal(str(body.get('price', product.price)))
            
            # If stock changes, log the inventory movement
            new_stock = int(body.get('stock', product.stock))
            if new_stock != product.stock:
                diff = new_stock - product.stock
                mov_type = InventoryLog.MovementType.IN if diff > 0 else InventoryLog.MovementType.OUT
                InventoryLog.objects.create(
                    product=product,
                    user=User.objects.first(),
                    quantity=abs(diff),
                    movement_type=mov_type,
                    reason="Modificación manual de stock"
                )
                product.stock = new_stock

            product.is_active = body.get('is_active', product.is_active)
            product.save()
            return JsonResponse({"status": "success"})

        elif request.method == 'DELETE':
            product.delete()
            return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def api_orders(request):
    """API for managing orders."""
    try:
        if request.method == 'GET':
            orders = Order.objects.all().order_by('-id')
            data = []
            for o in orders:
                items_list = []
                for item in o.items.all():
                    items_list.append({
                        "product_id": item.product.id,
                        "product_name": item.product.name,
                        "quantity": item.quantity,
                        "price": float(item.unit_price)
                    })
                data.append({
                    "id": o.id,
                    "user": o.client.username,
                    "status": o.status,
                    "status_display": o.get_status_display(),
                    "total_amount": float(o.total_amount),
                    "delivery_address": o.delivery_address,
                    "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
                    "items": items_list
                })
            return JsonResponse(data, safe=False)

        elif request.method == 'POST':
            body = json.loads(request.body)
            user = User.objects.first() # Use default admin user
            
            # Create Order
            order = Order.objects.create(
                client=user,
                status=body.get('status', Order.Status.PENDING),
                delivery_address=body.get('delivery_address', ''),
                total_amount=Decimal('0.00')
            )
            
            total = Decimal('0.00')
            # Add Items
            for item in body.get('items', []):
                prod = Product.objects.get(pk=item['product_id'])
                qty = int(item['quantity'])
                price = prod.price
                
                # Check stock
                if prod.stock < qty:
                    return JsonResponse({"status": "error", "message": f"Stock insuficiente para {prod.name}"}, status=400)
                
                # Deduct stock and log movement
                prod.stock -= qty
                prod.save()
                InventoryLog.objects.create(
                    product=prod,
                    user=user,
                    quantity=qty,
                    movement_type=InventoryLog.MovementType.OUT,
                    reason=f"Descuento por Pedido #{order.id}"
                )
                
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    quantity=qty,
                    unit_price=price
                )
                total += price * qty
            
            order.total_amount = total
            order.save()
            
            # Create Delivery entry if order is preparing/shipped/delivered
            if order.status in [Order.Status.ACCEPTED, Order.Status.ON_WAY, Order.Status.DELIVERED]:
                driver = User.objects.filter(role=User.Roles.DRIVER).first()
                Delivery.objects.create(
                    order=order,
                    driver=driver,
                    notes="Generado automáticamente al registrar pedido."
                )
                
            return JsonResponse({"status": "success", "id": order.id, "total": float(total)})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def api_order_status(request, pk):
    """Endpoint to update order status."""
    try:
        if request.method == 'PUT':
            order = Order.objects.get(pk=pk)
            body = json.loads(request.body)
            new_status = body['status']
            if new_status not in Order.Status.values:
                return JsonResponse({"status": "error", "message": "Estado no válido"}, status=400)
            
            order.status = new_status
            order.save()

            # Sync delivery details
            if new_status in [Order.Status.ACCEPTED, Order.Status.ON_WAY]:
                delivery, created = Delivery.objects.get_or_create(order=order)
                if created:
                    delivery.driver = User.objects.filter(role=User.Roles.DRIVER).first()
                    delivery.save()
            elif new_status == Order.Status.DELIVERED:
                delivery, _ = Delivery.objects.get_or_create(order=order)
                from django.utils import timezone
                delivery.delivered_at = timezone.now()
                delivery.save()

            return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def api_agencies(request):
    """API for listing agencies."""
    try:
        agencies = Agency.objects.all().order_by('id')
        data = []
        for a in agencies:
            data.append({
                "id": a.id,
                "name": a.name,
                "address": a.address,
                "manager": a.manager.username if a.manager else "No asignado",
                "is_active": a.is_active
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def api_inventory(request):
    """API for listing all stock logs and movement history."""
    try:
        logs = InventoryLog.objects.all().order_by('-created_at')
        data = []
        for log in logs:
            data.append({
                "id": log.id,
                "product_name": log.product.name,
                "quantity": log.quantity,
                "movement_type": log.movement_type,
                "movement_display": log.get_movement_type_display(),
                "reason": log.reason,
                "user": log.user.username if log.user else "Sistema",
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M")
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def api_deliveries(request):
    """API for listing active distribution and logistics info."""
    try:
        deliveries = Delivery.objects.all().order_by('-assigned_at')
        data = []
        for d in deliveries:
            data.append({
                "id": d.id,
                "order_id": d.order.id,
                "client_name": d.order.client.username,
                "delivery_address": d.order.delivery_address,
                "driver": d.driver.username if d.driver else "No asignado",
                "assigned_at": d.assigned_at.strftime("%Y-%m-%d %H:%M"),
                "delivered_at": d.delivered_at.strftime("%Y-%m-%d %H:%M") if d.delivered_at else None,
                "notes": d.notes,
                "status_display": d.order.get_status_display()
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# =====================================================================
# ADMIN AGENCIES CRUD
# =====================================================================

class AgencyCreateForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'})
    )
    nombre_empresa = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la empresa'})
    )
    direccion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dirección completa'})
    )
    telefono = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '591-XXXXXXX'})
    )
    email_contacto = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email de contacto (opcional)'})
    )
    notas_internas = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notas internas (opcional)'})
    )
    logo = forms.ImageField(required=False)
    latitud = forms.DecimalField(
        required=False, max_digits=9, decimal_places=6,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Latitud (opcional)'})
    )
    longitud = forms.DecimalField(
        required=False, max_digits=9, decimal_places=6,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Longitud (opcional)'})
    )


class AgencyEditForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['nombre_empresa', 'direccion', 'telefono', 'email_contacto', 'notas_internas', 'logo', 'latitud', 'longitud', 'activa']
        widgets = {
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'notas_internas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'latitud': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitud': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


def _send_agency_credentials_email(email, username, password, reset_url):
    """Sends login credentials to the new agency via email."""
    from django.core.mail import send_mail
    subject = "Bienvenido a Agua de Mesa Santiago — Credenciales de acceso a tu agencia"
    body = (
        f"Hola,\n\n"
        f"El administrador de Agua de Mesa Santiago ha creado tu cuenta de agencia.\n\n"
        f"Tus credenciales de acceso son:\n"
        f"  Usuario: {username}\n"
        f"  Contraseña: {password}\n\n"
        f"Puedes ingresar en: https://aquaflow.up.railway.app/login/\n"
        f"Te recomendamos cambiar tu contraseña en: {reset_url}\n\n"
        f"Si tienes alguna duda, contacta al administrador.\n\n"
        f"-- Equipo Agua de Mesa Santiago"
    )
    send_mail(subject, body, None, [email], fail_silently=True)


@login_required
@role_required('admin')
def admin_agencies(request):
    """List all agencies with order totals."""
    agencies = Agency.objects.select_related('usuario').annotate(
        total_pedidos=Count('agency_orders'),
        monto_total=Sum('agency_orders__total_amount')
    ).order_by('-fecha_creacion')
    return render(request, 'admin_panel/agencias.html', {'agencies': agencies})


@login_required
@role_required('admin')
def admin_agency_create(request):
    """Create a new agency user + agency profile and send credentials email."""
    import secrets
    if request.method == 'POST':
        form = AgencyCreateForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            # Validate unique username
            if User.objects.filter(username=d['username']).exists():
                form.add_error('username', 'Este nombre de usuario ya está en uso.')
                return render(request, 'admin_panel/agencia_form.html', {'form': form, 'title': 'Crear Nueva Agencia'})

            # Generate random password
            raw_password = secrets.token_urlsafe(10)

            # Create user with agency role
            user = User.objects.create_user(
                username=d['username'],
                email=d['email'],
                password=raw_password,
                role=User.Roles.AGENCY,
                is_staff=False,
                is_superuser=False,
            )

            # Determine contact email
            email_contacto = d.get('email_contacto') or d['email']

            # Create agency profile
            agency = Agency(
                usuario=user,
                nombre_empresa=d['nombre_empresa'],
                direccion=d['direccion'],
                telefono=d['telefono'],
                email_contacto=email_contacto,
                notas_internas=d.get('notas_internas', ''),
                latitud=d.get('latitud'),
                longitud=d.get('longitud'),
            )
            if request.FILES.get('logo'):
                agency.logo = request.FILES['logo']
            agency.save()

            # Build password reset URL for the email
            from django.urls import reverse
            reset_url = request.build_absolute_uri(reverse('password_reset'))

            # Send credentials email
            _send_agency_credentials_email(email_contacto, user.username, raw_password, reset_url)

            messages.success(
                request,
                f"Agencia '{agency.nombre_empresa}' creada. Se enviaron las credenciales a {email_contacto}."
            )
            return redirect('admin_agencies')
    else:
        form = AgencyCreateForm()
    return render(request, 'admin_panel/agencia_form.html', {'form': form, 'title': 'Crear Nueva Agencia'})


@login_required
@role_required('admin')
def admin_agency_detail(request, pk):
    """View agency detail, orders, and statistics."""
    agency = get_object_or_404(Agency, pk=pk)
    orders = Order.objects.filter(agency=agency).order_by('-created_at')
    total_pedidos = orders.count()
    monto_total = orders.filter(status=Order.Status.DELIVERED).aggregate(
        s=Sum('total_amount'))['s'] or Decimal('0.00')
    promedio = (monto_total / total_pedidos) if total_pedidos else Decimal('0.00')
    return render(request, 'admin_panel/agencia_detalle.html', {
        'agency': agency,
        'orders': orders,
        'total_pedidos': total_pedidos,
        'monto_total': monto_total,
        'promedio': promedio,
        'maps_key': __import__('os').environ.get('GOOGLE_MAPS_API_KEY', ''),
    })


@login_required
@role_required('admin')
def admin_agency_edit(request, pk):
    """Edit agency details (not the linked user)."""
    agency = get_object_or_404(Agency, pk=pk)
    if request.method == 'POST':
        form = AgencyEditForm(request.POST, request.FILES, instance=agency)
        if form.is_valid():
            form.save()
            messages.success(request, f"Agencia '{agency.nombre_empresa}' actualizada.")
            return redirect('admin_agency_detail', pk=agency.pk)
    else:
        form = AgencyEditForm(instance=agency)
    return render(request, 'admin_panel/agencia_form.html', {
        'form': form,
        'title': f'Editar Agencia — {agency.nombre_empresa}',
        'agency': agency,
    })


@login_required
@role_required('admin')
def admin_agency_toggle_active(request, pk):
    """Toggle agency active/inactive."""
    agency = get_object_or_404(Agency, pk=pk)
    agency.activa = not agency.activa
    agency.save()
    estado = 'activada' if agency.activa else 'desactivada'
    messages.success(request, f"Agencia '{agency.nombre_empresa}' {estado} exitosamente.")
    return redirect('admin_agencies')
