"""
Helpers for cart management that support both anonymous and authenticated users.
"""
from .models import Cart, CartItem


def _get_or_create_cart(request):
    """
    Return the Cart for the current request.
    - Authenticated users: look up by user (one-to-one).
    - Anonymous users: look up by session_key, creating the session first if needed.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        # Ensure the session exists so Django assigns a session key.
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
        return cart


def transfer_cart(request, user):
    """
    After login/registration, merge the anonymous session cart into the user's cart
    and delete the anonymous cart so nothing is duplicated.
    """
    if not request.session.session_key:
        return  # Nothing to transfer.

    session_key = request.session.session_key
    try:
        anon_cart = Cart.objects.get(session_key=session_key, user=None)
    except Cart.DoesNotExist:
        return  # No anonymous cart to merge.

    user_cart, _ = Cart.objects.get_or_create(user=user)

    for anon_item in anon_cart.items.all():
        existing = user_cart.items.filter(product=anon_item.product).first()
        if existing:
            existing.quantity += anon_item.quantity
            existing.save()
        else:
            CartItem.objects.create(
                cart=user_cart,
                product=anon_item.product,
                quantity=anon_item.quantity,
                price_at_time=anon_item.price_at_time,
            )

    anon_cart.delete()
