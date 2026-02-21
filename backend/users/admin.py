# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('full_name', 'email', 'national_id', 'phone_number')}),
        ('مجوزها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌ها', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'full_name', 'email', 'national_id', 'phone_number'),
        }),
    )
    list_display = ('username', 'full_name', 'email', 'national_id', 'phone_number', 'get_groups', 'is_staff')
    search_fields = ('username', 'full_name', 'email', 'national_id', 'phone_number')
    ordering = ('-date_joined',)
    filter_horizontal = ('groups', 'user_permissions',)

    def get_groups(self, obj):
        return obj.get_roles_display()
    get_groups.short_description = 'نقش‌ها'