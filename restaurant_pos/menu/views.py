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
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('order')
        return context
