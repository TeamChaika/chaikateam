from django.contrib import admin

from .models import Category, Spending, Agreed, Month


class SpendingAdmin(admin.ModelAdmin):
    model = Spending

    list_display = admin.ModelAdmin.list_display + (
        'category', 'department', 'user', 'amount', 'agreed', 'created_at',
        'month', 'year'
    )
    list_filter = (
        'department', 'category', 'user', 'agreed', 'created_at', 'month',
        'year'
    )


admin.site.register(Category)
admin.site.register(Month)
admin.site.register(Spending, SpendingAdmin)
admin.site.register(Agreed)
