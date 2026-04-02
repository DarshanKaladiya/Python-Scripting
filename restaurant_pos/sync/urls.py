from django.urls import path

from .views import offline_actions, pending_status

app_name = "sync"

urlpatterns = [
    path("offline-actions/", offline_actions, name="offline-actions"),
    path("pending-status/", pending_status, name="pending-status"),
]
