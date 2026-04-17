from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.decorators import chef_required, staff_required, pos_required
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Order
from .serializers import OrderSerializer
from tables.models import Table, FloorSection
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

    @action(detail=False, methods=['post'])
    def combine_tables(self, request):
        primary_id = request.data.get('primary_table_id')
        secondary_ids = request.data.get('secondary_table_ids', [])
        
        if not primary_id or not secondary_ids:
            return Response({'error': 'Primary and secondary table IDs required'}, status=status.HTTP_400_BAD_REQUEST)
            
        primary_table = get_object_or_404(Table, id=primary_id)
        secondary_tables = Table.objects.filter(id__in=secondary_ids)
        
        # 1. Get or Create Primary Order
        active_statuses = ['draft', 'awaiting_confirmation', 'kot_sent', 'preparing', 'ready']
        primary_order = Order.objects.filter(table=primary_table, status__in=active_statuses).first()
        
        if not primary_order:
            # Create a new draft order if none exists
            from django.utils import timezone
            import random
            order_num = f"ORD{int(timezone.now().timestamp())}{random.randint(100, 999)}"
            primary_order = Order.objects.create(
                order_number=order_num,
                table=primary_table,
                status='draft',
                waiter=request.user if request.user.is_authenticated else None
            )
            primary_table.status = 'occupied'
            primary_table.save()
            
        # 2. Merge Secondary Orders and Attach Tables
        for table in secondary_tables:
            # Find if this table has an active order
            sec_order = Order.objects.filter(table=table, status__in=active_statuses).first()
            if sec_order and sec_order.id != primary_order.id:
                # Move items to primary order
                for item in sec_order.items.all():
                    item.order = primary_order
                    item.save()
                # Cancel the old empty order
                sec_order.status = 'cancelled'
                sec_order.save()
            
            # Link table to the primary order
            primary_order.additional_tables.add(table)
            
            # Data for Snapping: Attach Table B to Table A
            table.attached_to = primary_table
            table.status = 'occupied'
            
            # Auto-Snap logic: Place Table B to the right of Table A
            # Assuming average table width is ~15% of canvas width
            table.y_pos = primary_table.y_pos
            table.x_pos = primary_table.x_pos + 12 # 12% shift for snapping
            
            table.save()
            
        primary_order.calculate_totals()
        return Response({'status': 'tables_combined', 'order_id': primary_order.id})

    @action(detail=True, methods=['post'])
    def split_tables(self, request, pk=None):
        order = self.get_object()
        
        # 1. Clear all attachments and reset secondary table statuses
        primary_table = order.table
        secondary_tables = list(order.additional_tables.all())
        
        for table in secondary_tables:
            if table:
                table.attached_to = None
                table.status = 'available' # Secondary tables become free
                table.x_pos -= 2 # Move away slightly
                table.save()
        
        # Reset primary table attachment but keep it occupied
        if primary_table:
            primary_table.attached_to = None
            primary_table.save()
        
        # 2. Clear many-to-many relationship
        order.additional_tables.clear()
        order.save()
        
        return Response({'status': 'tables_split'})

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

    @action(detail=False, methods=['post'])
    def update_item_status(self, request):
        item_id = request.data.get('item_id')
        new_status = request.data.get('status')
        
        from .models import OrderItem
        item = get_object_or_404(OrderItem, id=item_id)
        
        if new_status in dict(OrderItem.STATUS_CHOICES):
            item.status = new_status
            item.save()
            return Response({'status': 'updated', 'new_status': new_status})
        return Response({'error': 'invalid status'}, status=status.HTTP_400_BAD_REQUEST)

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
        station = self.request.GET.get('station', 'all')
        
        # Filtering orders that have items in the selected station
        active_statuses = ['kot_sent', 'preparing', 'ready']
        orders_qs = Order.objects.filter(status__in=active_statuses)
        
        if station != 'all':
            orders_qs = orders_qs.filter(items__menu_item__category__kitchen_station=station).distinct()
        
        context['orders'] = orders_qs.order_by('created_at').prefetch_related('items__menu_item__category')
        context['selected_station'] = station
        
        all_active = Order.objects.filter(status__in=['kot_sent', 'preparing', 'ready'])
        context['new_count'] = all_active.filter(status='kot_sent').count()
        context['prep_count'] = all_active.filter(status='preparing').count()
        
        # Calculate Capacity Load
        max_load = 20 
        load_score = (all_active.count() / max_load) * 100
        context['capacity_label'] = "HIGH" if load_score > 70 else "MEDIUM" if load_score > 30 else "OPTIMAL"
        context['load_percentage'] = min(load_score, 100)
        context['avg_prep_time'] = "12:45" 
        
        # HTMX Check
        if self.request.headers.get('HX-Request'):
            self.template_name = 'orders/includes/kds_grid.html'
            
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

