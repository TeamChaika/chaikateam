# Generated by Django 5.0.1 on 2024-01-26 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_auto_20220817_0150'),
        ('stores', '0001_initial')
    ]

    state_operations = [
        migrations.AlterField(
            model_name='user',
            name='stores',
            field=models.ManyToManyField(blank=True, to='stores.Store', verbose_name='склады'),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations
        )
    ]
