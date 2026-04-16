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
        
        # Determine if the user is a staff member (Admin, Cashier, Captain, Waiter, or Chef)
        is_staff = request.user.is_staff or (hasattr(request.user, 'role') and request.user.role in ['admin', 'cashier', 'captain', 'chef', 'waiter'])
        
        if is_staff:
            # Staff/POS orders go straight to kitchen unless explicitly set to completed (Direct Bill)
            data['status'] = data.get('status', 'kot_sent')
            if 'payment_status' not in data:
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
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            
            # Special logic for final states
            if new_status == 'completed' and order.payment_status == 'pending':
                order.payment_status = 'paid' # Assume paid if marked complete
                
            if new_status == 'kot_sent' and order.payment_status == 'pending':
                # Logic for KOT: if not paid yet, usually stays pending
                pass 
            
            # Optional: handle payment details if provided during settlement
            if 'payment_method' in request.data:
                order.payment_method = request.data['payment_method']
            if 'payment_status' in request.data:
                order.payment_status = request.data['payment_status']
            if 'customer_name' in request.data:
                order.customer_name = request.data['customer_name']
            if 'customer_phone' in request.data:
                order.customer_phone = request.data['customer_phone']
                
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
        tracking_uuid = request.query_params.get('tracking_uuid')
        
        if tracking_uuid:
            order = get_object_or_404(Order, tracking_uuid=tracking_uuid)
        elif order_number:
            order = get_object_or_404(Order, order_number=order_number)
        else:
            return Response({'error': 'No order identifier provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'id': order.id,
            'status': order.status,
            'order_type': order.order_type,
            'order_number': order.order_number,
            'display_status': order.get_status_display(),
            'total_amount': order.total_amount,
            'tracking_uuid': order.tracking_uuid
        })

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Returns orders that were placed by customers and are awaiting confirmation."""
        orders = Order.objects.filter(status='awaiting_confirmation').order_by('-created_at')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

@method_decorator(pos_required, name='dispatch')
class POSView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/pos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_table_id'] = self.request.GET.get('table_id')
        context['selected_order_id'] = self.request.GET.get('order_id')
        return context

@method_decorator(staff_required, name='dispatch')
class WaiterDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/waiter_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sections'] = FloorSection.objects.all().prefetch_related('tables')
        # Map tables to any active dine-in orders
        active_statuses = ['draft', 'awaiting_confirmation', 'kot_sent', 'preparing', 'ready']
        active_orders = Order.objects.filter(status__in=active_statuses, order_type='dine_in')
        table_order_map = {order.table_id: order for order in active_orders if order.table_id}
        context['table_order_map'] = table_order_map
        return context


@method_decorator(staff_required, name='dispatch')
class KDSView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/kds.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_active = Order.objects.filter(status__in=['kot_sent', 'preparing', 'ready'])
        
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

class LiveOrderTrackerView(TemplateView):
    template_name = 'orders/live_tracker.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_uuid = self.kwargs.get('qr_uuid')
        
        # Smart Resolver: Try to find a specific Order first (Takeaway or Direct Link)
        active_order = Order.objects.filter(tracking_uuid=target_uuid).first()
        table = None
        
        if active_order:
            table = active_order.table
        else:
            # Try to find a Table QR (Static)
            table = Table.objects.filter(qr_code_uuid=target_uuid).first()
            if table:
                # Find the most recent active order for this table
                active_order = Order.objects.filter(
                    table=table, 
                    status__in=['awaiting_confirmation', 'kot_sent', 'preparing', 'ready', 'completed']
                ).order_by('-created_at').first()
        
        if not active_order and not table:
            raise Http404("Invalid tracking ID")

        # If the order is "completed", we only show it if it was created in the last 2 hours
        from django.utils import timezone
        import datetime
        if active_order and active_order.status == 'completed':
            if active_order.updated_at < timezone.now() - datetime.timedelta(hours=2):
                active_order = None

        context['table'] = table
        context['order'] = active_order
        
        # Upsell / Recommendations logic (Category Matching)
        if active_order:
            # Get IDs of categories already represented in the order
            ordered_cat_ids = active_order.items.values_list('menu_item__category_id', flat=True).distinct()
            
            # Suggest items from categories NOT yet ordered (e.g. if they ordered Main, suggest Dessert/Bev)
            recommendations = MenuItem.objects.filter(
                is_active=True
            ).exclude(
                category_id__in=ordered_cat_ids
            ).order_by('?')[:4]
            
            # Fallback if they ordered everything or no other categories exist
            if not recommendations.exists():
                recommendations = MenuItem.objects.filter(is_active=True).exclude(
                    id__in=active_order.items.values_list('menu_item_id', flat=True)
                ).order_by('?')[:4]
                
            context['recommendations'] = recommendations
        else:
            # Static recommendations for new sessions
            context['recommendations'] = MenuItem.objects.filter(is_active=True).order_by('?')[:4]
            
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

