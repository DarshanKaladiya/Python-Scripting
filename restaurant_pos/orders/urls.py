from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import POSView, OrderViewSet, KDSView, SelfOrderView, LiveOrderTrackerView, generate_invoice, WaiterDashboardView

app_name = 'orders'

router = DefaultRouter()
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('pos/', POSView.as_view(), name='pos_home'),
    path('waiter/', WaiterDashboardView.as_view(), name='waiter_dashboard'),
    path('kds/', KDSView.as_view(), name='kds'),
    path('self-order/', SelfOrderView.as_view(), name='self_order'),
    path('track/<uuid:qr_uuid>/', LiveOrderTrackerView.as_view(), name='live_tracker'),
    path('invoice/<int:order_id>/', generate_invoice, name='generate_invoice'),
    path('api/', include(router.urls)),
]

