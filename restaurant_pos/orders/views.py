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

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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

