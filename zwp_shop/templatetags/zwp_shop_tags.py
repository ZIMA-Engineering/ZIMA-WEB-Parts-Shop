from django import template
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


register = template.Library()


@register.inclusion_tag('zwp_shop/cart_preview.html', takes_context=True)
def zwp_cart(context):
    return context


@register.filter
def currency(v):
    return settings.ZWP_CURRENCY(v)


@register.inclusion_tag('zwp_shop/order_steps.html', takes_context=True)
def zwp_order_steps(context):
    steps = (
        ('shipping_payment', _('Shipping and payment method')),
        ('billing', _('Billing and delivery')),
        ('confirm', _('Confirmation')),
    )
    context['steps'] = steps
    return {
        'steps': steps,
        'current_step': context['wizard']['steps'].current
    }
