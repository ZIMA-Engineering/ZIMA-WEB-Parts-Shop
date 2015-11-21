from .models import EmptyCart, Cart


def cart(request):
    c = None

    if request.session.session_key and request.session['zwp_cart']:
        try:
            c = Cart.objects.get(pk=request.session['zwp_cart'])

        except Cart.DoesNotExist:
            pass

    if not c:
        c = EmptyCart()

    return {
        'cart': c
    }
