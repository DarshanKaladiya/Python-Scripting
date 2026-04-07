from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import POSView, OrderViewSet, KDSView

app_name = 'orders'

router = DefaultRouter()
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('pos/', POSView.as_view(), name='pos_home'),
    path('kds/', KDSView.as_view(), name='kds'),
    path('api/', include(router.urls)),
]

