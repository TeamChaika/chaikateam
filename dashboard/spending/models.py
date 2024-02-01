from django.db import models

from departments.models import Department
from authentication.models import User


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=128, unique=True, null=False, verbose_name='Название'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Agreed(models.Model):
    name = models.CharField(
        max_length=128, null=False, unique=True, verbose_name='Наименование'
    )

    def __str__(self):
        return self.name


class Month(models.Model):
    name = models.CharField(
        max_length=16, null=False, unique=True, verbose_name='Название'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'учетный месяц'
        verbose_name_plural = 'учетные месяцы'


class Spending(models.Model):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, to_field='name',
        verbose_name='Заведение', null=False
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, to_field='name',
        verbose_name='Категория', null=False
    )
    user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, to_field='username',
        verbose_name='Пользователь', null=False
    )
    name = models.CharField(
        max_length=128, null=False, verbose_name='Наименование'
    )
    amount = models.IntegerField(null=False, verbose_name='Сумма')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    agreed = models.ForeignKey(
        Agreed, on_delete=models.DO_NOTHING, to_field='name',
        verbose_name='Согласовано', null=False, default='Управляющий'
    )
    month = models.ForeignKey(
        Month, to_field="name", on_delete=models.SET_NULL, null=True,
        verbose_name='Учетный месяц', default=None
    )
    year = models.IntegerField(
        null=True, verbose_name='Учетный год', default=None
    )

    class Meta:
        verbose_name = 'расход'
        verbose_name_plural = 'расходы'

    def __str__(self):
        return self.name
