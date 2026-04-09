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
        
        # Smart Table Detection
        table_id = self.request.GET.get('table')
        if table_id:
            try:
                table = Table.objects.get(id=table_id)
                context['table'] = table
                # Check for active dine-in order on this table
                active_order = Order.objects.filter(
                    table=table, 
                    status__in=['draft', 'awaiting_confirmation', 'kot_sent', 'preparing', 'ready']
                ).first()
                context['active_order'] = active_order
            except (Table.DoesNotExist, ValueError):
                pass
                
        return context
