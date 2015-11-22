from django import forms
from django.forms.widgets import HiddenInput
from django.forms import modelformset_factory
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import IntegrityError, transaction
from zwp.models import Directory
from .models import Part, CartItem


class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ('ds_name', 'dir_path', 'name')
        widgets = {
            'ds_name': HiddenInput(),
            'dir_path': HiddenInput(),
            'name': HiddenInput()
        }
    
    def clean(self):
        data = super(PartForm, self).clean()

        self.dir = Directory.from_path(data['ds_name'], data['dir_path'], load=True)

        if not self.dir:
            raise forms.ValidationError('invalid data source or directory')

        self.part = None

        for p in self.dir.parts:
            if p.name == data['name']:
                self.part = p
                break
        else:
            raise forms.ValidationError("part '{}' does not exist".format(data['part']))

        self.instance.part = self.part

        return data


class ItemAddForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ('quantity',)

    def __init__(self, data=None, initial={}, *args, **kwargs):
        part_args = []
        part_data = {}
        part_initial = {}

        for f in ['ds_name', 'dir_path', 'name']:
            if data and f in data:
                part_data[f] = data[f]

            if initial and f in initial:
                part_initial[f] = initial[f]

        if part_data:
            part_args.append(part_data)

        self.part_form = PartForm(*part_args, initial=part_initial)

        if data:
            args = list(args)
            args.insert(0, data)

        super(ItemAddForm, self).__init__(*args, initial=initial, **kwargs)

    def clean(self):
        data = super(ItemAddForm, self).clean()

        if not self.part_form.instance.part.available:
            raise forms.ValidationError("part '{}' is not for sale".format(
                self.part_form.instance.part.label
            ))

        self.instance.unit_cost = self.part_form.instance.part.cost

        return data
    
    def is_valid(self):
        return self.part_form.is_valid() and super(ItemAddForm, self).is_valid() 

    def save(self):
        # Every part is in the database just once
        try:
            with transaction.atomic():
                self.part_form.save()

            self.instance.part = self.part_form.instance

        except IntegrityError:
            self.instance.part = Part.objects.existing(
                self.part_form.instance.hash,
                self.part_form.part
            )

        # There is one CartItem for every Part, so if it already exists, do not create
        # new one, but update its quantity.
        try:
            with transaction.atomic():
                self.instance.save()

        except IntegrityError:
            item = CartItem.objects.get(
                cart=self.instance.cart,
                part=self.instance.part
            )
            item.quantity += self.instance.quantity
            item.touch()

        self.instance.cart.touch()


class ItemEditForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ('quantity',)

    def __init__(self, *args, **kwargs):
        super(ItemEditForm, self).__init__(*args, **kwargs)

        self.part = self.instance.part.part


CartItemFormSet = modelformset_factory(
    CartItem,
    form=ItemEditForm,
    extra=0,
    can_delete=True
)
