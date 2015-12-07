from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from formtools.wizard.views import SessionWizardView
from .models import Cart, Address, Order
from .forms import ItemAddForm, CartItemFormSet, ShippingPaymentOrderForm, \
                   BillingOrderForm, ConfirmOrderForm
from .utils import get_cart, get_or_create_cart, get_shipping, get_payment
from .mail import new_order as mail_new_order


def cart_show(request):
    qs = get_or_create_cart(request.session).cartitem_set.all()

    if request.method == 'POST':
        formset = CartItemFormSet(request.POST, queryset=qs)

        if formset.is_valid():
            with transaction.atomic():
                formset.save()

            return redirect('zwp_cart_show')

    else:
        formset = CartItemFormSet(queryset=qs)

    return render(request, 'zwp_shop/cart.html', {
        'formset': formset
    })


@transaction.atomic
def cart_add(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    form = ItemAddForm(request.POST)

    if not form.is_valid():
        return HttpResponse('u suck')

    form.instance.cart = get_or_create_cart(request.session)
    form.save()

    if request.META['HTTP_REFERER']:
        return redirect(request.META['HTTP_REFERER'])

    return redirect(form.instance.part.part.dir.url)



def order_confirmed(request, order_id):
    return render(request, 'zwp_shop/order/confirmed.html', {
        'order': get_object_or_404(Order, pk=order_id)
    })


class OrderWizard(SessionWizardView):
    form_list = (
        ('shipping_payment', ShippingPaymentOrderForm),
        ('billing', BillingOrderForm),
        ('confirm', ConfirmOrderForm)
    )

    def get_template_names(self):
        return [{
            'shipping_payment': 'zwp_shop/order/shipping_payment.html',
            'billing': 'zwp_shop/order/billing.html',
            'confirm': 'zwp_shop/order/confirm.html'
        }[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        data = super(OrderWizard, self).get_context_data(form, **kwargs)
        cart = get_cart(self.request.session)
        
        if self.steps.current == 'confirm':
            delivery = self.get_form(
                'shipping_payment',
                self.get_cleaned_data_for_step('shipping_payment')
            )
            billing = self.get_form('billing', self.get_cleaned_data_for_step('billing'))

            shipping = get_shipping(delivery.data['shipping'])
            payment = get_payment(delivery.data['payment'])

            total_cost = cart.total_cost
            total_cost += shipping['cost']
            total_cost += payment['cost']

            data.update({
                'shipping': shipping,
                'payment': payment,
                'billing': self._billing_data(billing),
                'same_delivery_address': billing.data['same_address'],
                'total_cost': total_cost
            })
        
        return data

    @transaction.atomic
    def done(self, form_list, form_dict, **kwargs):
        delivery_form = form_dict['shipping_payment']
        billing_form = form_dict['billing']

        order = billing_form.instance
        order.cart = get_cart(self.request.session)
        order.shipping = delivery_form.cleaned_data['shipping']
        order.payment = delivery_form.cleaned_data['payment']
        order.note = form_dict['confirm'].cleaned_data['note']

        billing_form.save()

        billing_form.to_address('billing').save()

        if not billing_form.cleaned_data['same_address']:
            billing_form.to_address('delivery').save()

        mail_new_order(self.request, order)

        del self.request.session['zwp_cart']

        return redirect('zwp_order_confirmed', order.pk)
    
    def _billing_data(self, form):
        ret = {}

        for fieldset in form.fieldsets:
            ret[fieldset.name] = []

            for f in fieldset:
                if f.name == 'same_address':
                    continue
                
                ret[fieldset.name].append({
                    'label': f.label,
                    'value': form.data[f.name]
                })
        
        return ret
