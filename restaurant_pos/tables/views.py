from django.shortcuts import render
from rest_framework import viewsets
from .models import Table, FloorSection
from .serializers import TableSerializer, FloorSectionSerializer
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from orders.models import Order

from .models import Table, FloorSection, FloorDecor
from .serializers import TableSerializer, FloorSectionSerializer, FloorDecorSerializer

from rest_framework.response import Response
from rest_framework.decorators import action

class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer

    @action(detail=True, methods=['post'])
    def mark_available(self, request, pk=None):
        table = self.get_object()
        table.status = 'available'
        table.attached_to = None
        table.save()
        
        # Also find any active orders linked to this table and unlink them
        active_statuses = ['draft', 'awaiting_confirmation', 'kot_sent', 'preparing', 'ready']
        
        # 1. If it's a primary table on an order
        Order.objects.filter(table=table, status__in=active_statuses).update(table=None)
        
        # 2. If it's an additional table on an order
        orders_with_extra = Order.objects.filter(additional_tables=table, status__in=active_statuses)
        for order in orders_with_extra:
            order.additional_tables.remove(table)
            
        return Response({'status': 'table_cleared'})

class FloorDecorViewSet(viewsets.ModelViewSet):
    queryset = FloorDecor.objects.all()
    serializer_class = FloorDecorSerializer

class FloorSectionViewSet(viewsets.ModelViewSet):
    queryset = FloorSection.objects.all()
    serializer_class = FloorSectionSerializer

class FloorMapView(LoginRequiredMixin, TemplateView):
    template_name = 'tables/floor_map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sections'] = FloorSection.objects.all().prefetch_related('tables', 'decor_items')
        
        # Map tables to any active dine-in orders (Primary or Combined)
        active_statuses = ['draft', 'awaiting_confirmation', 'kot_sent', 'preparing', 'ready']
        active_orders = Order.objects.filter(status__in=active_statuses, order_type='dine_in').prefetch_related('additional_tables')
        
        table_order_map = {}
        for order in active_orders:
            if order.table_id:
                table_order_map[order.table_id] = order
            for extra in order.additional_tables.all():
                table_order_map[extra.id] = order
                
        context['table_order_map'] = table_order_map
        
        # HTMX check
        if self.request.headers.get('HX-Request'):
            self.template_name = 'tables/includes/map_grid.html'
            
        return context
