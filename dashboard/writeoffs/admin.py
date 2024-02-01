from django.contrib import admin
from .models import Writeoff, WriteoffItem, WriteoffReason

# Register your models here.
admin.site.register(WriteoffReason)
admin.site.register(Writeoff)
admin.site.register(WriteoffItem)
