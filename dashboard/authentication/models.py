from django.db import models
from django.contrib.auth.models import AbstractUser, \
    UserManager as BaseUserManager

from departments.models import Department
from waybills.models import Store


class UserManager(BaseUserManager):
    def get(self, *args, **kwargs):
        return super().select_related(
            'department'
        ).prefetch_related(
            'stores'
        ).get(*args, **kwargs)


class User(AbstractUser):
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True,
        verbose_name='Заведение', blank=True
    )
    stores = models.ManyToManyField(Store, verbose_name="склады", blank=True)
    telegram_id = models.BigIntegerField(
        null=True, unique=True, verbose_name='Telegram ID', blank=True
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        permissions = [
            ('can_view_dashboard', 'Просмотр дэшборда'),
            ('can_view_hungry', 'Просмотр отчётов Hungry Bird 2.0'),
            ('can_add_waybills', 'Создание накладных'),
            ('can_view_waybills', 'Просмотр накладных'),
            ('can_view_guests', 'Просмотр гостей'),
            ('can_register_users', 'Взаимодействие с заявками на регистрацию'),
            ('can_add_writeoffs', 'Создание списаний'),
            ('can_view_writeoffs', 'Просмотр списаний'),
            ('is_disposer', 'Управляющий'),
            ('is_accountant', 'Бухгалтер')
        ]


class RegisterRequest(models.Model):
    username = models.CharField(max_length=150, unique=True, null=False)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True,
        verbose_name='Заведение', blank=True
    )
    password = models.CharField(max_length=128, null=False)
    telegram_id = models.BigIntegerField(blank=True, null=True, db_index=True)

    objects = models.Manager()

    class Meta:
        verbose_name = 'запрос на регистрацию'
        verbose_name_plural = 'запросы на регистрацию'
