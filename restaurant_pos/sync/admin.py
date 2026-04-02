from django.contrib import admin

from .models import OfflineAction, Terminal

admin.site.register(Terminal)
admin.site.register(OfflineAction)

# Register your models here.
