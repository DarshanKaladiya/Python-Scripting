from django.urls import path

from .views import kds_screen, update_item_status

app_name = "kitchen"

urlpatterns = [
    path("", kds_screen, name="screen"),
    path("api/items/<int:kot_item_id>/status/", update_item_status, name="update-item-status"),
]
