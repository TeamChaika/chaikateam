from django.db import models
from time import time
from stores.models import Store


class Waybill(models.Model):
    store = models.ForeignKey(
        Store, on_delete=models.DO_NOTHING, null=False, verbose_name='Склад'
    )
    counteragent = models.ForeignKey(
        Store, on_delete=models.DO_NOTHING, null=False,
        verbose_name='Контрагент', related_name='counteragent'
    )
    comment = models.TextField(
        null=True, default=None, verbose_name='Комментарий'
    )
    status = models.CharField(max_length=16, null=False, default='Created')
    created_by = models.ForeignKey(
        'authentication.User', on_delete=models.DO_NOTHING, null=False
    )
    processed_by = models.ForeignKey(
        'authentication.User', on_delete=models.DO_NOTHING, null=True,
        related_name='processed_by', default=None
    )
    created_at = models.BigIntegerField(null=False, default=time)
    processed_at = models.BigIntegerField(null=True, default=None)

    class Meta:
        db_table = 'waybills'
        verbose_name = 'накладная'
        verbose_name_plural = 'накладные'


class WaybillItem(models.Model):
    waybill = models.ForeignKey(Waybill, on_delete=models.CASCADE, null=False)
    product_id = models.UUIDField(null=False, db_index=True)
    amount = models.FloatField(null=False, default=0.0)

    class Meta:
        db_table = 'waybills_items'
