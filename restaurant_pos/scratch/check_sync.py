import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from tables.models import Table
from orders.models import Order

print("--- TABLE STATUS CHECK ---")
for table in Table.objects.all():
    active_orders = Order.objects.filter(table=table, status__in=['draft', 'awaiting_confirmation', 'kot_sent', 'preparing', 'ready'])
    print(f"Table: {table.name} | Status: {table.status} | Active Orders: {active_orders.count()}")
    for order in active_orders:
        print(f"  - Order {order.order_number} | Status: {order.status}")

print("\n--- COMPLETED ORDERS WITH OCCUPIED TABLES ---")
stuck_orders = Order.objects.filter(status='completed', table__status='occupied')
for order in stuck_orders:
    print(f"Stuck: Order {order.order_number} is COMPLETED but Table {order.table.name} is OCCUPIED")
