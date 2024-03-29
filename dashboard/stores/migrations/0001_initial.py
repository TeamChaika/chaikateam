# Generated by Django 5.0.1 on 2024-01-26 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    state_operations = [
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.CharField(max_length=36, primary_key=True, serialize=False, verbose_name='Идентификатор')),
                ('name', models.CharField(max_length=128, unique=True, verbose_name='Наименование')),
            ],
            options={
                'verbose_name': 'склад',
                'verbose_name_plural': 'склады',
                'db_table': 'stores',
            },
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
