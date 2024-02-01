from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = UserAdmin.list_display + ('department',)
    list_filter = UserAdmin.list_filter + ('department', 'stores')
    fieldsets = UserAdmin.fieldsets + (
        ('Заведение', {'fields': ('department',)}),
        ('Telegram', {'fields': ('telegram_id',)}),
        ('Cклады', {'fields': ('stores',)})
    )
    filter_horizontal = ('groups', 'user_permissions', 'stores',)


admin.site.register(User, CustomUserAdmin)
