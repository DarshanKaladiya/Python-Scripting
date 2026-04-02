from django.contrib import admin

from .models import MenuCategory, MenuItem, ModifierGroup, ModifierOption

admin.site.register(MenuCategory)
admin.site.register(MenuItem)
admin.site.register(ModifierGroup)
admin.site.register(ModifierOption)

# Register your models here.
