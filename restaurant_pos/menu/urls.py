from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MenuItemViewSet, CustomerMenuView

app_name = 'menu'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', MenuItemViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('menu/', CustomerMenuView.as_view(), name='customer_menu'),
]
