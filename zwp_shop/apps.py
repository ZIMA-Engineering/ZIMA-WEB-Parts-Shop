from django.apps import AppConfig

class ZwpShopConfig(AppConfig):
    name = 'zwp_shop'
    verbose_name = 'ZIMA-WEB-Parts E-Shop'

    def ready(self):
        import zwp_shop.signals
        import zwp_shop.zwp_extends
