from django.urls import path
from .views import FloorMapView

app_name = 'tables'

urlpatterns = [
    path('floor/', FloorMapView.as_view(), name='floor_map'),
]
