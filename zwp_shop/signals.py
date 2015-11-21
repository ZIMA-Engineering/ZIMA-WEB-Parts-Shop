from django.dispatch import receiver
from zwp.signals import *


@receiver(part_meta_load)
def load_part_meta(sender, name, cfg, **kwargs):
    ret = {}

    if cfg.has_option(name, 'available'):
        ret['available'] = cfg.getboolean(name, 'available')

    if cfg.has_option(name, 'cost'):
        ret['cost'] = cfg.getint(name, 'cost')
    
    if cfg.has_option(name, 'unit'):
        ret['unit'] = cfg[name]['unit']

    return ret
