from django.contrib import admin

from .models import AppSetting, AuditLog, OutletProfile, PaymentMethod, Printer, TaxRate

admin.site.register(OutletProfile)
admin.site.register(TaxRate)
admin.site.register(PaymentMethod)
admin.site.register(Printer)
admin.site.register(AppSetting)
admin.site.register(AuditLog)

# Register your models here.
