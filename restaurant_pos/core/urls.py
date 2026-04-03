from django.urls import path

from .views import dashboard, dashboard_summary_api

app_name = "core"

urlpatterns = [
    path("api/dashboard/summary/", dashboard_summary_api, name="dashboard-summary"),
    path("", dashboard, name="dashboard"),
]
