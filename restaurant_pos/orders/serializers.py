from rest_framework import serializers
from .models import Order, OrderItem
from menu.models import MenuItem

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.ReadOnlyField(source='menu_item.name')
    
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'menu_item_name', 'quantity', 'price', 'notes']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'order_type', 'status', 'payment_method', 'payment_status', 'guest_count', 'customer_name', 'customer_phone', 'table', 'waiter', 'customer_user', 'subtotal', 'cgst', 'sgst', 'tax', 'service_charge', 'total_amount', 'items', 'tracking_uuid']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Auto-assign customer if authenticated and not already set
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role in ['admin', 'cashier', 'captain', 'waiter']:
                validated_data['waiter'] = request.user
            elif (request.user.role == 'customer' or request.user.is_superuser) and not validated_data.get('customer_user'):
                validated_data['customer_user'] = request.user

        # Calculate subtotal directly from input data to avoid DB query lag
        subtotal = sum(item['price'] * item['quantity'] for item in items_data)
        
        order = Order.objects.create(**validated_data)
        order.subtotal = subtotal # Seed the subtotal
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Final calculation (GST, Total)
        order.calculate_totals()
        return order
