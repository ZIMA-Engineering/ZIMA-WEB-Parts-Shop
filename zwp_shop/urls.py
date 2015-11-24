from django.conf.urls import include, url
from . import views

urlpatterns = [
#    url('^(?P<ds>[a-zA-Z0-9\-_]+)/(?P<path>.*)$', views.show_path, name='zwp_dir')
    url('^cart$', views.cart_show, name='zwp_cart_show'),
    url('^cart/add$', views.cart_add, name='zwp_cart_add'),
    url(r'^order$', views.OrderWizard.as_view(), name='zwp_order'),
    url(r'^order/confirmed/(?P<order_id>\d+)$', views.order_confirmed, name='zwp_order_confirmed'),
]
