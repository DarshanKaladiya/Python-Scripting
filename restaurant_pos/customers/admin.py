from django.contrib import admin

from .models import Customer, LoyaltyRule

admin.site.register(Customer)
admin.site.register(LoyaltyRule)

# Register your models here.
