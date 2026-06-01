from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
import json
from decimal import Decimal

# Import models
from products.models import Product
from orders.models import Order, OrderItem
from inventory.models import InventoryLog
from agencies.models import Agency
from distribution.models import Delivery
from accounts.models import User

# Helper to serialize decimals
def serialize_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

@csrf_exempt
def seed_data(request):
    """Seeds sample data into the database if empty to make the dashboard beautiful immediately."""
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
        o1 = Order.objects.create(user=user, status=Order.Status.DELIVERED, total_amount=Decimal("120.00"), delivery_address="Calle Florida #10")
        OrderItem.objects.create(order=o1, product=p1, quantity=10, price_at_time=Decimal("12.00"))
        Delivery.objects.create(order=o1, driver=driver, notes="Entregado a tiempo. Todo conforme.", delivered_at=o1.created_at)

        # Order 2 (Shipped)
        o2 = Order.objects.create(user=user, status=Order.Status.SHIPPED, total_amount=Decimal("45.00"), delivery_address="Av. Aroma #200")
        OrderItem.objects.create(order=o2, product=p3, quantity=1, price_at_time=Decimal("45.00"))
        Delivery.objects.create(order=o2, driver=driver, notes="En ruta de distribución.")

        # Order 3 (Preparing)
        o3 = Order.objects.create(user=user, status=Order.Status.PREPARING, total_amount=Decimal("210.00"), delivery_address="Agencia Norte")
        OrderItem.objects.create(order=o3, product=p2, quantity=14, price_at_time=Decimal("15.00"))

    return JsonResponse({"status": "success", "message": "Datos de prueba creados exitosamente."})

def api_dashboard_stats(request):
    """Returns dashboard numeric statistics."""
    # Run seed automatically if empty
    if Product.objects.count() == 0:
        try:
            seed_data(request)
        except Exception:
            pass

    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    active_deliveries = Order.objects.filter(status__in=[Order.Status.PREPARING, Order.Status.SHIPPED]).count()
    
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

@csrf_exempt
def api_products(request):
    """API for managing products."""
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
        try:
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
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
def api_product_detail(request, pk):
    """API to edit or delete a specific product."""
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Producto no encontrado"}, status=404)

    if request.method == 'PUT':
        try:
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
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    elif request.method == 'DELETE':
        product.delete()
        return JsonResponse({"status": "success"})

@csrf_exempt
def api_orders(request):
    """API for managing orders."""
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
                    "price": float(item.price_at_time)
                })
            data.append({
                "id": o.id,
                "user": o.user.username,
                "status": o.status,
                "status_display": o.get_status_display(),
                "total_amount": float(o.total_amount),
                "delivery_address": o.delivery_address,
                "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
                "items": items_list
            })
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            body = json.loads(request.body)
            user = User.objects.first() # Use default admin user
            
            # Create Order
            order = Order.objects.create(
                user=user,
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
                    price_at_time=price
                )
                total += price * qty
            
            order.total_amount = total
            order.save()
            
            # Create Delivery entry if order is preparing/shipped/delivered
            if order.status in [Order.Status.PREPARING, Order.Status.SHIPPED, Order.Status.DELIVERED]:
                driver = User.objects.filter(role=User.Roles.DRIVER).first()
                Delivery.objects.create(
                    order=order,
                    driver=driver,
                    notes="Generado automáticamente al registrar pedido."
                )
                
            return JsonResponse({"status": "success", "id": order.id, "total": float(total)})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
def api_order_status(request, pk):
    """Endpoint to update order status."""
    if request.method == 'PUT':
        try:
            order = Order.objects.get(pk=pk)
            body = json.loads(request.body)
            new_status = body['status']
            if new_status not in Order.Status.values:
                return JsonResponse({"status": "error", "message": "Estado no válido"}, status=400)
            
            order.status = new_status
            order.save()

            # Sync delivery details
            if new_status in [Order.Status.PREPARING, Order.Status.SHIPPED]:
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
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

def api_agencies(request):
    """API for listing agencies."""
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

def api_inventory(request):
    """API for listing all stock logs and movement history."""
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

def api_deliveries(request):
    """API for listing active distribution and logistics info."""
    deliveries = Delivery.objects.all().order_by('-assigned_at')
    data = []
    for d in deliveries:
        data.append({
            "id": d.id,
            "order_id": d.order.id,
            "client_name": d.order.user.username,
            "delivery_address": d.order.delivery_address,
            "driver": d.driver.username if d.driver else "No asignado",
            "assigned_at": d.assigned_at.strftime("%Y-%m-%d %H:%M"),
            "delivered_at": d.delivered_at.strftime("%Y-%m-%d %H:%M") if d.delivered_at else None,
            "notes": d.notes,
            "status_display": d.order.get_status_display()
        })
    return JsonResponse(data, safe=False)
