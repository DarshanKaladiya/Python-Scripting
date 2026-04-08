from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.decorators import chef_required
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Order
from .serializers import OrderSerializer
from tables.models import Table
from menu.models import Category, MenuItem

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        # Determine status based on payment method
        payment_method = data.get('payment_method', 'cash')
        if payment_method == 'cash':
            data['status'] = 'awaiting_confirmation'
            data['payment_status'] = 'pending'
        else:
            data['status'] = 'kot_sent'
            data['payment_status'] = 'paid'

        # Smart Table Assignment for Dine-in
        order_type = data.get('order_type', 'takeaway')
        if order_type == 'dine_in' and not data.get('table'):
            guest_count = int(data.get('guest_count', 1))
            # Find the best available table that fits the guest count
            available_table = Table.objects.filter(
                status='available', 
                capacity__gte=guest_count
            ).order_by('capacity').first()
            
            if available_table:
                data['table'] = available_table.id
                # Mark as occupied immediately for self-orders
                available_table.status = 'occupied'
                available_table.save()
            else:
                return Response({'error': 'No suitable table available at the moment.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            order = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            if new_status == 'kot_sent':
                order.payment_status = 'paid' # Assuming confirmation means payment received for cash
            order.save()
            return Response({'status': 'updated'})
        return Response({'error': 'invalid status'}, status=status.HTTP_400_BAD_REQUEST)

class POSView(TemplateView):
    template_name = 'orders/pos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_table_id'] = self.request.GET.get('table_id')
        context['selected_order_id'] = self.request.GET.get('order_id')
        return context

@method_decorator(chef_required, name='dispatch')
class KDSView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/kds.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(status__in=['kot_sent', 'preparing']).order_by('created_at')
        return context

class SelfOrderView(TemplateView):
    template_name = 'orders/self_order.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('order')
        context['menu_items'] = MenuItem.objects.filter(is_active=True)
        return context

