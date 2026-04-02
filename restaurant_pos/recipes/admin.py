from django.contrib import admin

from .models import Recipe, RecipeLine

admin.site.register(Recipe)
admin.site.register(RecipeLine)

# Register your models here.
