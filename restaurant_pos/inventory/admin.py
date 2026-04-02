from django.contrib import admin

from .models import Ingredient, PurchaseEntry, PurchaseItem, StockAdjustment, StockLedger, Unit, Vendor, WastageEntry

admin.site.register(Unit)
admin.site.register(Vendor)
admin.site.register(Ingredient)
admin.site.register(PurchaseEntry)
admin.site.register(PurchaseItem)
admin.site.register(StockLedger)
admin.site.register(WastageEntry)
admin.site.register(StockAdjustment)

# Register your models here.
