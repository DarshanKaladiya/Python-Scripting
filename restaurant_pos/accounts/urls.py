from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import RoleBasedLoginView

app_name = 'accounts'

urlpatterns = [
    path('login/', RoleBasedLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='accounts:login'), name='logout'),
]
