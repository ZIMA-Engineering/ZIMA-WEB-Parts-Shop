from zwp.models import Part
from .forms import ItemAddForm


part_methods = ['available', 'cart_form']


@property
def available(self):
    if 'available' in self._meta:
        avail = self._meta['available']
        
    else:
        avail = True

    if not avail:
        return False
 
    if 'cost' not in self._meta:
        return False

    return True


@property
def cart_form(self):
    if hasattr(self, '_cart_form'):
        return self._cart_form

    self._cart_form = ItemAddForm(initial={
        'ds_name': self.ds.name,
        'dir_path': self._dir.full_path,
        'name': self._name,
        'quantity': 1
    })

    return self._cart_form


for m in part_methods:
    setattr(Part, m, locals()[m])


def part_prop(name):
    @property
    def inner(self):
        try:
            return self._dir.metadata_for(self.base_name)[name]

        except KeyError:
            return None

    return inner

part_props = ['cost', 'unit']

for p in part_props:
    setattr(Part, p, part_prop(p))

