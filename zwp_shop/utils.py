from .models import Cart


def get_or_create_cart(session):
    if not session.session_key or not session['zwp_cart']:
        cart = Cart.objects.create()
        session['zwp_cart'] = cart.pk

    else:
        try:
            cart = Cart.objects.get(pk=session['zwp_cart'])

        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            session['zwp_cart'] = cart.pk

    return cart

