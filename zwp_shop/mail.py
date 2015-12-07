from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import mail_managers, send_mail
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from .utils import replace_language
from .settings import ZWP_SHOP_MANAGER_LANGUAGE_CODE


def new_order(request, order):
    site = get_current_site(request)

    vars = {
        'order': order,
    }

    # Mail managers about the new order
    with replace_language(ZWP_SHOP_MANAGER_LANGUAGE_CODE):
        mail_managers(
            _('[{0}] New order').format(site.name),
            render_to_string('zwp_shop/email/manager/new_order.txt', vars),
            html_message=render_to_string('zwp_shop/email/manager/new_order.html', vars)
        )

    # Mail the customer
    send_mail(
        _('[{0}] Order confirmation').format(site.name),
        render_to_string('zwp_shop/email/user/order_confirmed.txt', vars),
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
        html_message=render_to_string('zwp_shop/email/user/order_confirmed.html', vars)
    )
