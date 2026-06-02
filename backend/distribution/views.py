from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

from core.decorators import role_required
from orders.models import Order
from ratings.models import Rating
from .models import Delivery

@login_required
@role_required('driver')
def driver_dashboard(request):
    # Pending orders that need a driver
    pending_orders = Order.objects.filter(
        status=Order.Status.PENDING,
        driver__isnull=True
    ).order_by('-created_at')
    
    # Active orders assigned to this driver
    active_orders = Order.objects.filter(
        driver=request.user,
        status__in=[Order.Status.ACCEPTED, Order.Status.ON_WAY]
    ).order_by('-created_at')

    return render(request, 'driver/dashboard.html', {
        'pending_orders': pending_orders,
        'active_orders': active_orders,
        'pusher_key': settings.PUSHER_KEY,
        'pusher_cluster': settings.PUSHER_CLUSTER
    })

@login_required
@role_required('driver')
def driver_accept_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, status=Order.Status.PENDING, driver__isnull=True)
    
    order.driver = request.user
    order.status = Order.Status.ACCEPTED
    order.save()
    
    # Create or update Delivery log
    Delivery.objects.update_or_create(
        order=order,
        defaults={'driver': request.user}
    )
    
    messages.success(request, f"¡Has aceptado el pedido #{order.id}! Ya puedes iniciar la entrega.")
    return redirect('driver_dashboard')

@login_required
@role_required('driver')
def driver_update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, driver=request.user)
    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')
    
    if new_status in [Order.Status.ON_WAY, Order.Status.DELIVERED]:
        order.status = new_status
        order.save()
        
        # Update delivery log notes and timestamps
        delivery, _ = Delivery.objects.get_or_create(order=order)
        if notes:
            delivery.notes = notes
        if new_status == Order.Status.DELIVERED:
            delivery.delivered_at = timezone.now()
        delivery.save()
        
        messages.success(request, f"Estado del pedido #{order.id} actualizado a '{order.get_status_display()}'.")
    else:
        messages.error(request, "Estado no válido para actualización.")
        
    return redirect('driver_dashboard')

@login_required
@role_required('driver')
def driver_history(request):
    deliveries = Delivery.objects.filter(
        driver=request.user,
        order__status=Order.Status.DELIVERED
    ).order_by('-delivered_at')
    
    # Calculate average score for completed deliveries
    ratings = Rating.objects.filter(driver=request.user)
    avg_score = sum(r.score for r in ratings) / len(ratings) if ratings.exists() else 0.0
    
    # Match ratings to their delivery order
    for d in deliveries:
        d.rating = ratings.filter(order=d.order).first()
        
    return render(request, 'driver/historial.html', {
        'deliveries': deliveries,
        'avg_score': avg_score,
        'ratings_count': ratings.count()
    })
