from django.contrib import admin

from .models import DiningSection, RestaurantTable, WaiterAssignment

admin.site.register(DiningSection)
admin.site.register(RestaurantTable)
admin.site.register(WaiterAssignment)

# Register your models here.
