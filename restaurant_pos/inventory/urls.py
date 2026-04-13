from django.urls import path
from .views import AdminDashboardView, InventoryListView, SalesReportView

app_name = 'inventory'

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('list/', InventoryListView.as_view(), name='inventory_list'),
    path('sales/', SalesReportView.as_view(), name='sales_report'),
]
