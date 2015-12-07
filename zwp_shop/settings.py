from django.conf import settings


ZWP_SHOP_MANAGER_LANGUAGE_CODE = getattr(
    settings,
    'ZWP_SHOP_MANAGER_LANGUAGE_CODE',
    settings.LANGUAGE_CODE
)
