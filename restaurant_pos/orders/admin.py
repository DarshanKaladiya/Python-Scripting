from django.contrib import admin
from .models import Order, OrderItem, KitchenOrderTicket

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'order_type', 'status', 'total_amount', 'created_at')
    list_filter = ('order_type', 'status', 'created_at')
    search_fields = ('order_number',)
    inlines = [OrderItemInline]

@admin.register(KitchenOrderTicket)
class KitchenOrderTicketAdmin(admin.ModelAdmin):
    list_display = ('kot_number', 'order', 'created_at', 'is_printed')
    list_filter = ('is_printed',)
