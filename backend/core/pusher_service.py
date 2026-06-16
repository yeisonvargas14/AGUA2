import pusher
from django.conf import settings

def get_pusher_client():
    if not settings.PUSHER_APP_ID or not settings.PUSHER_KEY:
        return None
    try:
        return pusher.Pusher(
            app_id=settings.PUSHER_APP_ID,
            key=settings.PUSHER_KEY,
            secret=settings.PUSHER_SECRET,
            cluster=settings.PUSHER_CLUSTER,
            ssl=True
        )
    except Exception:
        return None

def notify_new_order(order):
    client = get_pusher_client()
    if not client:
        return False
    try:
        data = {
            'order_id': order.id,
            'client': order.client.get_full_name() or order.client.username or order.client.telefono,
            'address': order.delivery_address,
            'total': float(order.total_amount),
            'items_count': order.items.count()
        }
        client.trigger('pedidos', 'nuevo-pedido', data)
        client.trigger('nuevo_pedido_admin', 'nuevo-pedido', data)
        client.trigger('drivers', 'new-order', data)
        return True
    except Exception:
        return False
