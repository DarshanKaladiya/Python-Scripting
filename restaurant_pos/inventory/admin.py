from django.contrib import admin
from .models import Unit, Supplier, RawMaterial

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_code')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')

@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'unit', 'current_stock', 'reorder_level')
    list_filter = ('unit', 'supplier')
    search_fields = ('name', 'sku')
