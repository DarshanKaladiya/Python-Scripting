from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("POS Access", {"fields": ("role", "phone_number", "pin_code", "is_shift_active")}),
    )
    list_display = ("username", "first_name", "last_name", "role", "is_staff", "is_shift_active")
    list_filter = ("role", "is_staff", "is_shift_active")

# Register your models here.
