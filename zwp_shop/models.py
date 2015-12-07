from django.db import models
from django.db.models import Sum, F
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, get_language
import hashlib
import os
from zwp.models import Directory


class EmptyCart:
    @property
    def size(self):
        return 0

    @property
    def total_cost(self):
        return 0


class Cart(models.Model):
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), null=True)
   
    def __str__(self):
        return 'Cart #{}'.format(self.pk)

    @property
    def size(self):
        return self.cartitem_set.count()

    @property
    def total_cost(self):
        return self.cartitem_set.aggregate(
            total_cost=Sum(F('unit_cost') * F('quantity'))
        )['total_cost']

    def touch(self, save=True):
        self.updated_at = timezone.now()

        if save:
            self.save()


class PartManager(models.Manager):
    def existing(self, hash, part):
        p = self.get(hash=hash)
        p.part = part
        return p


class Part(models.Model):
    ds_name = models.CharField(_('data source'), max_length=50)
    dir_path = models.CharField(_('directory'), max_length=500)
    name = models.CharField(_('part'), max_length=255)
    hash = models.CharField(_('hash'), max_length=64, unique=True)
    objects = PartManager()

    @property
    def part(self):
        if hasattr(self, '_part'):
            return self._part

        self._part = None
        d = Directory.from_path(self.ds_name, self.dir_path, load=True)

        if not d:
            return None
        
        for p in d.parts:
            if p.name == self.name:
                self._part = p
                break
        
        return self._part

    @part.setter
    def part(self, v):
        self._part = v

    def save(self, *args, **kwargs):
        if not self.pk:
            self.hash = hashlib.sha256(''.join(os.path.join(
                self.ds_name,
                self.dir_path,
                self.name
            )).encode('utf-8')).hexdigest()

        super(Part, self).save(*args, **kwargs)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart)
    part = models.ForeignKey(Part)
    unit_cost = models.PositiveIntegerField(_('unit cost'))
    quantity = models.PositiveIntegerField(_('quantity'))
    added_at = models.DateTimeField(_('added at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), null=True)

    class Meta:
        unique_together = (('cart', 'part'),)

    @property
    def total_cost(self):
        return self.unit_cost * self.quantity

    def touch(self, save=True):
        self.updated_at = timezone.now()

        if save:
            self.save()


class Order(models.Model):
    cart = models.OneToOneField(Cart)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
   
    ic = models.IntegerField(_('ic'), blank=True, null=True)
    email = models.CharField(_('e-mail'), max_length=255)
    phone = models.CharField(_('telephone number'), max_length=13)
    note = models.TextField(_('note'), blank=True)

    language = models.CharField(_('language'), max_length=6)

    shipping = models.CharField(_('shipping method'), max_length=30)
    shipping_label = models.CharField(_('shipping label'), max_length=50)
    shipping_cost = models.PositiveIntegerField(_('shipping cost'))
   
    payment = models.CharField(_('payment method'), max_length=30)
    payment_label = models.CharField(_('payment label'), max_length=50)
    payment_cost = models.PositiveIntegerField(_('payment cost'))

    total_cost = models.PositiveIntegerField(_('total cost'), default=0)
    
    def save(self, *args, **kwargs):
        is_new = not self.pk

        if is_new:
            from .utils import get_shipping, get_payment

            self.language = get_language()

            shipping = get_shipping(self.shipping)
            self.shipping_label = shipping['label']
            self.shipping_cost = shipping['cost']

            payment = get_payment(self.payment)
            self.payment_label = payment['label']
            self.payment_cost = payment['cost']

            self.total_cost = self.cart.total_cost + self.shipping_cost + self.payment_cost

        super(Order, self).save(*args, **kwargs)

    @property
    def billing(self):
        if getattr(self, '_billing', False):
            return self._billing

        self._billing = self.address_set.get(role='billing')
        return self._billing

    @property
    def delivery(self):
        if getattr(self, '_delivery', False):
            return self._delivery

        try:
            self._delivery = self.address_set.get(role='delivery')

        except Address.DoesNotExist:
            self._delivery = self.billing

        return self._delivery

    def has_same_delivery(self):
        return self.billing == self.delivery


ADDRESS_ROLES = (
    ('billing', _('billing address')),
    ('delivery', _('delivery address'))
)


class Address(models.Model):
    order = models.ForeignKey(Order)
    role = models.CharField(_('role'), max_length=15, choices=ADDRESS_ROLES)
    full_name = models.CharField(_('full name'), max_length=255)
    street = models.CharField(_('street'), max_length=255)
    city = models.CharField(_('city'), max_length=255)
    postal_code = models.CharField(_('postal code'), max_length=5)

    class Meta:
        unique_together = (('order', 'role'),)
