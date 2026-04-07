from django.contrib import admin
from .models import Category, MenuItem, RecipeIngredient

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'color_code')
    list_editable = ('order',)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'item_type', 'is_active')
    list_filter = ('category', 'item_type', 'is_active')
    search_fields = ('name', 'sku')
    inlines = [RecipeIngredientInline]
