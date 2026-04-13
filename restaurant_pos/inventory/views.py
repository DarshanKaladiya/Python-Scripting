from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.decorators import admin_required
from django.utils.decorators import method_decorator
from orders.models import Order
from inventory.models import RawMaterial
from django.db.models import Sum, F
from django.db import models

@method_decorator(admin_required, name='dispatch')
class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_sales'] = Order.objects.filter(status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['order_count'] = Order.objects.count()
        context['low_stock_items'] = RawMaterial.objects.filter(current_stock__lte=F('reorder_level'))
        context['recent_orders'] = Order.objects.all().order_by('-created_at')[:5]
        return context

@method_decorator(admin_required, name='dispatch')
class InventoryListView(LoginRequiredMixin, TemplateView):
    template_name = 'admin/inventory_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materials'] = RawMaterial.objects.all().order_by('name')
        return context

@method_decorator(admin_required, name='dispatch')
class SalesReportView(LoginRequiredMixin, TemplateView):
    template_name = 'admin/sales_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(status='completed').order_by('-created_at')
        context['total_sales'] = context['orders'].aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        return context
