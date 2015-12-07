from django import forms
from django.forms.widgets import HiddenInput
from django.forms import modelformset_factory
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.db import IntegrityError, transaction
from form_utils.forms import BetterModelFormMetaclass, BetterModelForm
from collections import OrderedDict
from zwp.models import Directory
from .models import Part, CartItem, Order, Address, ADDRESS_ROLES


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
    quantity = forms.IntegerField(min_value=1)

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
    quantity = forms.IntegerField(min_value=1)
    
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


def settings_to_choices(s):
    return [
        (m['name'], '{} ({})'.format(
            m['label'],
            settings.ZWP_CURRENCY(m['cost'])
        )) for m in s
    ]


class ShippingPaymentOrderForm(forms.Form):
    shipping = forms.ChoiceField(
        label=_('shipping'),
        choices=settings_to_choices(settings.ZWP_SHIPPING),
        widget=forms.RadioSelect
    )
    payment = forms.ChoiceField(
        label=_('payment'),
        choices=settings_to_choices(settings.ZWP_PAYMENT),
        widget=forms.RadioSelect
    )


address_fields = (
    ('full_name', lambda r: forms.CharField(label=_('Full name'), max_length=255, required=r)),
    ('street', lambda r: forms.CharField(label=_('Street'), max_length=255, required=r)),
    ('city', lambda r: forms.CharField(label=_('City'), max_length=255, required=r)),
    ('postal_code', lambda r: forms.CharField(label=_('Postal code'), max_length=5, required=r)),
)


def order_attr_names(t):
    return ['_'.join([t, n]) for n, _ in address_fields]


class MyMeta(BetterModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        for t, required in {'billing': True, 'delivery': False}.items():
            for name, field in address_fields:
                attrs[ '_'.join([t, name]) ] = field(required)

        return super(MyMeta, cls).__new__(cls, name, bases, attrs)


class BillingOrderForm(BetterModelForm, metaclass=MyMeta):
    same_address = forms.BooleanField(
        label=_('Use the billing address'),
        required=False,
        initial=True
    )

    class Meta:
        model = Order
        fieldsets = [
            ('billing', {
                'legend': _('Billing information'),
                'fields': order_attr_names('billing') + ['ic', 'email', 'phone']
            }),
            ('delivery', {
                'legend': _('Delivery address'),
                'fields': ['same_address'] + order_attr_names('delivery')
            }),
        ]
        widgets = {
            'ic': forms.TextInput
        }

    def clean(self):
        data = super(BillingOrderForm, self).clean()
        
        if not data.get('same_address', False):
            for f, _ in address_fields:
                field_name = '_'.join(['delivery', f])

                if field_name not in data or not data[field_name]:
                    self.add_error(field_name, __('This field is required.'))

    def to_address(self, role):
        kwargs = {
            'order': self.instance,
            'role': role
        }

        for f, _ in address_fields:
            kwargs[f] = self.cleaned_data['_'.join([role, f])]

        return Address(**kwargs)
        

class ConfirmOrderForm(forms.Form):
    note = forms.CharField(label=_('Note'), widget=forms.Textarea, required=False)
    confirm = forms.BooleanField(label=_('Confirm'))
