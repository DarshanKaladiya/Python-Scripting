from django.contrib import admin
from .models import FloorSection, Table

@admin.register(FloorSection)
class FloorSectionAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'status', 'capacity', 'x_pos', 'y_pos', 'shape')
    list_filter = ('section', 'status', 'shape')
    fieldsets = (
        (None, {
            'fields': ('name', 'section', 'status', 'capacity', 'qr_code_uuid')
        }),
        ('Spatial Layout', {
            'fields': ('x_pos', 'y_pos', 'width', 'height', 'shape'),
            'description': 'Position is in percentage (0-100) and dimensions in pixels.'
        }),
    )
