# Generated by Django 5.0.1 on 2024-01-26 16:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0002_update_refs'),
        ('stores', '0001_initial'),
        ('authentication', '0003_update_refs'),
        ('writeoffs', '0006_update_refs')
    ]

    state_operations = [
        migrations.DeleteModel('Store')
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations
        )
    ]