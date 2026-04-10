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
        fields = ['id', 'order_number', 'order_type', 'status', 'payment_method', 'payment_status', 'guest_count', 'customer_name', 'customer_phone', 'table', 'waiter', 'subtotal', 'cgst', 'sgst', 'tax', 'service_charge', 'total_amount', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Calculate subtotal directly from input data to avoid DB query lag
        subtotal = sum(item['price'] * item['quantity'] for item in items_data)
        
        order = Order.objects.create(**validated_data)
        order.subtotal = subtotal # Seed the subtotal
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Final calculation (GST, Total)
        order.calculate_totals()
        return order
