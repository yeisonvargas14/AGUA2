"""
Context processors for the orders app.
Injects cart_count into every template context so the navbar badge
works for both authenticated and anonymous users.
"""
from .cart_helpers import _get_or_create_cart


def cart_count(request):
    """Return the number of distinct product lines in the active cart."""
    try:
        cart = _get_or_create_cart(request)
        count = cart.items.count()
    except Exception:
        count = 0
    return {'cart_count': count}
