from django.urls import path

from .views import POSLoginView, POSLogoutView

app_name = "accounts"

urlpatterns = [
    path("login/", POSLoginView.as_view(), name="login"),
    path("logout/", POSLogoutView.as_view(), name="logout"),
]
