from rest_framework import viewsets
from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from accounts.decorators import customer_required

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('order', 'name')
    serializer_class = CategorySerializer

class MenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MenuItem.objects.filter(is_active=True)
    serializer_class = MenuItemSerializer

class CustomerMenuView(ListView):
    model = MenuItem
    template_name = 'menu/customer_menu.html'
    context_object_name = 'menu_items'

    def get_queryset(self):
        return MenuItem.objects.filter(is_active=True).select_related('category')

    def get_context_data(self, **kwargs):
        from tables.models import Table
        from orders.models import Order
        
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('order')
        
        # Smart Active Order Detection
        table_id = self.request.GET.get('table')
        active_order = None
        
        # Priority 1: Table-based detection (Dine-in)
        if table_id:
            try:
                table = Table.objects.get(id=table_id)
                context['table'] = table
                active_order = Order.objects.filter(
                    table=table, 
                    status__in=['draft', 'awaiting_confirmation', 'kot_sent', 'preparing', 'ready', 'completed']
                ).order_by('-created_at').first()
            except (Table.DoesNotExist, ValueError):
                pass
        
        # Priority 2: UUID-based detection (Direct Link / Takeaway Tracking)
        if not active_order:
            order_uuid = self.request.GET.get('track')
            if order_uuid:
                active_order = Order.objects.filter(tracking_uuid=order_uuid).first()

        # If order is completed, only show it if recent (last 2 hours)
        from django.utils import timezone
        import datetime
        if active_order and active_order.status == 'completed':
            if active_order.updated_at < timezone.now() - datetime.timedelta(hours=2):
                active_order = None

        context['active_order'] = active_order
        return context
