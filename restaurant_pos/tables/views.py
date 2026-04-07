from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Table, FloorSection
from orders.models import Order

class FloorMapView(LoginRequiredMixin, TemplateView):
    template_name = 'tables/floor_map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sections'] = FloorSection.objects.all().prefetch_related('tables')
        # Map tables to any active dine-in orders
        active_orders = Order.objects.filter(status__in=['draft', 'kot_sent', 'preparing', 'ready'], order_type='dine_in')
        table_order_map = {order.table_id: order for order in active_orders if order.table_id}
        context['table_order_map'] = table_order_map
        return context
