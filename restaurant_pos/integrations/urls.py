from django.urls import path

from .views import provider_order_webhook

app_name = "integrations"

urlpatterns = [
    path("<str:provider>/orders/", provider_order_webhook, name="provider-order-webhook"),
]
