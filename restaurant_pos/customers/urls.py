from django.urls import path

from .views import lookup_customer

app_name = "customers"

urlpatterns = [
    path("lookup/", lookup_customer, name="lookup"),
]
