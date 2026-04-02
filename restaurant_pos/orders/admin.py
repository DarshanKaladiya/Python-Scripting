from django.contrib import admin

from .models import KOTItem, KitchenOrderTicket, Order, OrderItem, Payment

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(KitchenOrderTicket)
admin.site.register(KOTItem)
admin.site.register(Payment)

# Register your models here.
