from time import time
from django.db import models
from stores.models import Store


class WriteoffReason(models.Model):
    name = models.CharField(
        max_length=128, null=False, unique=True, verbose_name='Наименование'
    )
    account_id = models.UUIDField(
        null=True, default=None,
        verbose_name='Идентификатор счёта'
    )

    class Meta:
        db_table = 'writeoffs_reasons'
        verbose_name = 'причина'
        verbose_name_plural = 'причины'

    def __str__(self):
        return self.name


class Writeoff(models.Model):
    store = models.ForeignKey(
        Store, on_delete=models.DO_NOTHING, null=False, verbose_name='Склад')
    reason = models.ForeignKey(
        WriteoffReason, on_delete=models.DO_NOTHING, to_field='name',
        verbose_name='Причина', default=None, null=True
    )
    comment = models.TextField(
        null=True, default=None, verbose_name='Комментарий')
    status = models.CharField(max_length=16, null=False, default='Created')
    created_by = models.ForeignKey(
        'authentication.User', on_delete=models.DO_NOTHING, null=False
    )
    processed_by = models.ForeignKey(
        'authentication.User', on_delete=models.DO_NOTHING, null=True,
        related_name='writeoff_processed_by', default=None
    )
    created_at = models.BigIntegerField(null=False, default=time)
    processed_at = models.BigIntegerField(null=True, default=None)

    class Meta:
        db_table = 'writeoffs'
        verbose_name = 'списание'
        verbose_name_plural = 'списания'


class WriteoffItem(models.Model):
    writeoff = models.ForeignKey(
        Writeoff, on_delete=models.CASCADE, null=False)
    product_id = models.UUIDField(null=False, db_index=True)
    amount = models.FloatField(null=False, default=0.0)

    class Meta:
        db_table = 'writeoffs_items'
