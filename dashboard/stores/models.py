from django.db import models


class Store(models.Model):
    id = models.UUIDField(
        auto_created=False, primary_key=True, serialize=False,
        verbose_name='ID'
    )
    name = models.CharField(
        max_length=128, null=False, verbose_name='Наименование', unique=True
    )

    class Meta:
        db_table = 'stores'
        verbose_name = 'склад'
        verbose_name_plural = 'склады'

    def __str__(self):
        return self.name
