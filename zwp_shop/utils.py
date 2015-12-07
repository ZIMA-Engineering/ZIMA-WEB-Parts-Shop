from django.conf import settings
from django.utils import translation
from django.utils.translation import get_language
from .models import Cart


def get_cart(session):
    if not session.session_key or 'zwp_cart' not in session:
        raise Cart.DoesNotExist('The session does not have a corresponding cart')

    return Cart.objects.get(pk=session['zwp_cart'])


def get_or_create_cart(session):
    if not session.session_key or 'zwp_cart' not in session:
        cart = Cart.objects.create()
        session['zwp_cart'] = cart.pk

    else:
        try:
            cart = Cart.objects.get(pk=session['zwp_cart'])

        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            session['zwp_cart'] = cart.pk

    return cart


def get_shipping(name):
    for s in settings.ZWP_SHIPPING:
        if s['name'] == name:
            return s

    return None

def get_payment(name):
    for s in settings.ZWP_PAYMENT:
        if s['name'] == name:
            return s

    return None


class replace_language:
    """
    Run a block of code with different active language.
    """
    def __init__(self, code):
        self.code = code

    def __enter__(self):
        self.orig_code = get_language()
        self.replaced = self.orig_code != self.code

        if self.replaced:
            translation.activate(self.code)

    def __exit__(self, *_):
        if self.replaced:
            translation.activate(self.orig_code)
