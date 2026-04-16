from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

class RoleBasedLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if user.role == 'admin':
            return reverse_lazy('inventory:admin_dashboard')
        elif user.role == 'chef':
            return reverse_lazy('orders:kds')
        elif user.role == 'customer':
            return reverse_lazy('menu:customer_menu')
        elif user.role == 'waiter':
            return reverse_lazy('orders:waiter_dashboard')
        elif user.role in ['cashier', 'captain']:
            return reverse_lazy('orders:pos_home')
        return reverse_lazy('orders:pos_home') # Default
