from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.decorators import chef_required, staff_required
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
        
        # Determine status based on payment method and user role
        payment_method = data.get('payment_method', 'cash')
        # Determine if the user is a staff member (Admin, Cashier, Captain, or Chef)
        is_staff = request.user.is_staff or (hasattr(request.user, 'role') and request.user.role in ['admin', 'cashier', 'captain', 'chef'])
        
        if is_staff:
            # Staff/POS orders go straight to kitchen
            data['status'] = data.get('status', 'kot_sent')
            data['payment_status'] = 'pending' if payment_method == 'cash' else 'paid'
        else:
            # Customer self-orders need confirmation if not pre-paid
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
                order.payment_status = 'paid'
            order.save()
                
            return Response({'status': 'updated'})
        return Response({'error': 'invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_items(self, request, pk=None):
        order = self.get_object()
        items_data = request.data.get('items', [])
        
        if not items_data:
            return Response({'error': 'No items provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .models import OrderItem
        for item_data in items_data:
            # item_data should contain menu_item (id), quantity, and price
            OrderItem.objects.create(
                order=order,
                menu_item_id=item_data['menu_item'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
        
        # Recalculate totals after adding items
        order.calculate_totals()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def check_status(self, request):
        order_number = request.query_params.get('order_number')
        if not order_number:
            return Response({'error': 'No order number provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        order = get_object_or_404(Order, order_number=order_number)
        return Response({
            'id': order.id,
            'status': order.status,
            'display_status': order.get_status_display(),
            'total_amount': order.total_amount
        })

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Returns orders that were placed by customers and are awaiting confirmation."""
        orders = Order.objects.filter(status='awaiting_confirmation').order_by('-created_at')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

class POSView(TemplateView):
    template_name = 'orders/pos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_table_id'] = self.request.GET.get('table_id')
        context['selected_order_id'] = self.request.GET.get('order_id')
        return context

@method_decorator(staff_required, name='dispatch')
class KDSView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/kds.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_active = Order.objects.filter(status__in=['kot_sent', 'preparing'])
        
        context['orders'] = all_active.order_by('created_at')
        context['new_count'] = all_active.filter(status='kot_sent').count()
        context['prep_count'] = all_active.filter(status='preparing').count()
        
        # Calculate Capacity Load
        max_load = 20 # Threshold for high load
        load_score = (all_active.count() / max_load) * 100
        context['capacity_label'] = "HIGH" if load_score > 70 else "MEDIUM" if load_score > 30 else "OPTIMAL"
        context['load_percentage'] = min(load_score, 100)
        
        # Simulated Avg Prep Time (Real would use completed orders)
        context['avg_prep_time'] = "12:45" 
        
        return context

class SelfOrderView(TemplateView):
    template_name = 'orders/self_order.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('order')
        context['menu_items'] = MenuItem.objects.filter(is_active=True)
        return context

def generate_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Ensure totals are calculated before printing
    order.calculate_totals()
    return render(request, 'orders/invoice.html', {'order': order})

