from django.urls import path
from . import views

urlpatterns = [
    # Change 'views.dashboard' to 'views.price_comparison_chart'
    path('', views.price_comparison_chart, name='comparison_chart'),
]