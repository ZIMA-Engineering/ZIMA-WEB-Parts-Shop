from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.db import transaction
from .models import Cart
from .forms import ItemAddForm, CartItemFormSet
from .utils import get_or_create_cart


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
