from django.conf.urls import include, url
from . import views

urlpatterns = [
#    url('^(?P<ds>[a-zA-Z0-9\-_]+)/(?P<path>.*)$', views.show_path, name='zwp_dir')
    url('^cart/add$', views.add_part_to_cart, name='zwp_add_part')
]
