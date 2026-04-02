from django.urls import path

from .views import summary_report

app_name = "reporting"

urlpatterns = [
    path("", summary_report, name="summary"),
]
