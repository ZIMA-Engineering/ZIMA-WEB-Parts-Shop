from django import template
from django.conf import settings


register = template.Library()


@register.inclusion_tag('zwp_shop/cart.html', takes_context=True)
def zwp_cart(context):
    return context

@register.filter
def currency(v):
    return settings.ZWP_CURRENCY(v)
