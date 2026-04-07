from django.urls import path
from .views import AdminDashboardView

app_name = 'inventory'

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
]
