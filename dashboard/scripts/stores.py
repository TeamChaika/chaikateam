from core.iiko import iiko_api
from stores.models import Store


def run():
    stores = set(Store.objects.all().values_list('id', flat=True))
    iiko_stores = iiko_api.get_stores()
    new = []
    for store in iiko_stores:
        if store['id'] not in stores:
            new.append(Store(id=store['id'], name=store['name']))
    if new:
        Store.objects.bulk_create(new)
