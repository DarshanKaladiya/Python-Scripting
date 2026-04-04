from django.urls import path

from .views import (
    add_item_api,
    cancel_order_api,
    complete_prepaid_order_view,
    confirm_self_service_cash_order_view,
    create_order_api,
    hold_order_api,
    menu_search,
    order_status_api,
    pos_screen,
    receipt_view,
    send_kot_api,
    self_service_screen,
    settle_order_api,
    submit_self_service_order_api,
)

app_name = "orders"

urlpatterns = [
    path("", pos_screen, name="pos"),
    path("self-service/", self_service_screen, name="self-service"),
    path("receipt/<int:order_id>/", receipt_view, name="receipt"),
    path("api/menu-search/", menu_search, name="menu-search"),
    path("api/orders/create/", create_order_api, name="create-order"),
    path("api/self-service/orders/submit/", submit_self_service_order_api, name="submit-self-service-order"),
    path("api/orders/<int:order_id>/items/add/", add_item_api, name="add-item"),
    path("api/orders/<int:order_id>/send-kot/", send_kot_api, name="send-kot"),
    path("api/orders/<int:order_id>/settle/", settle_order_api, name="settle-order"),
    path("api/orders/<int:order_id>/hold/", hold_order_api, name="hold-order"),
    path("api/orders/<int:order_id>/cancel/", cancel_order_api, name="cancel-order"),
    path("api/orders/<int:order_id>/status/", order_status_api, name="order-status"),
    path("orders/<int:order_id>/confirm-self-service/", confirm_self_service_cash_order_view, name="confirm-self-service"),
    path("orders/<int:order_id>/complete-prepaid/", complete_prepaid_order_view, name="complete-prepaid"),
]
