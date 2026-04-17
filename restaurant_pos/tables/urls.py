from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FloorMapView, TableViewSet, FloorSectionViewSet, FloorDecorViewSet

app_name = 'tables'

router = DefaultRouter()
router.register(r'tables', TableViewSet)
router.register(r'sections', FloorSectionViewSet)
router.register(r'decor', FloorDecorViewSet)

urlpatterns = [
    path('floor/', FloorMapView.as_view(), name='floor_map'),
    path('api/', include(router.urls)),
]
