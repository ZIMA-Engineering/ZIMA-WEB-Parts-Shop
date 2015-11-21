from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.db import transaction
from .models import Cart
from .forms import ItemForm


@transaction.atomic
def add_part_to_cart(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    form = ItemForm(request.POST)

    if not form.is_valid():
        print(form.erroes)
        return HttpResponse('u suck')

    if not request.session.session_key or not request.session['zwp_cart']:
        cart = Cart.objects.create()
        request.session['zwp_cart'] = cart.pk

    else:
        try:
            cart = Cart.objects.get(pk=request.session['zwp_cart'])

        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['zwp_cart'] = cart.pk
    
    form.instance.cart = cart
    form.save()

    if request.META['HTTP_REFERER']:
        return redirect(request.META['HTTP_REFERER'])

    return redirect(form.instance.part.part.dir.url)
