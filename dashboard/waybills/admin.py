from django.contrib import admin
from .models import Waybill, WaybillItem


admin.site.register(Waybill)
admin.site.register(WaybillItem)
