from django.urls import path

from .views import open_table_order, table_management_screen, transfer_table_order

app_name = "floor"

urlpatterns = [
    path("", table_management_screen, name="management"),
    path("tables/<int:table_id>/open/", open_table_order, name="open-table-order"),
    path("orders/<int:order_id>/transfer/", transfer_table_order, name="transfer-order"),
]
