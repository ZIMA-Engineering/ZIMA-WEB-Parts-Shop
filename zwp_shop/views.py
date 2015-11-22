from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.db import transaction
from .models import Cart
from .forms import ItemForm
from .utils import get_or_create_cart


@transaction.atomic
def add_part_to_cart(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    form = ItemForm(request.POST)

    if not form.is_valid():
        return HttpResponse('u suck')

    form.instance.cart = get_or_create_cart(request.session)
    form.save()

    if request.META['HTTP_REFERER']:
        return redirect(request.META['HTTP_REFERER'])

    return redirect(form.instance.part.part.dir.url)
