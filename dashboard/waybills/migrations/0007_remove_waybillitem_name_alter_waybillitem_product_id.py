# Generated by Django 5.0.1 on 2024-01-29 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0006_waybill_processed_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='waybillitem',
            name='name',
        ),
        migrations.AlterField(
            model_name='waybillitem',
            name='product_id',
            field=models.UUIDField(db_index=True),
        ),
    ]
