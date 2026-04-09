from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderItem
from menu.models import RecipeIngredient
from tables.models import Table

@receiver(post_save, sender=Order)
def sync_table_status(sender, instance, **kwargs):
    """Synchronizes table status with the order status."""
    if instance.table:
        active_statuses = ['draft', 'awaiting_confirmation', 'kot_sent', 'preparing', 'ready']
        
        if instance.status == 'completed':
            instance.table.status = 'available'
            instance.table.save()
        elif instance.status in active_statuses and instance.order_type == 'dine_in':
            instance.table.status = 'occupied'
            instance.table.save()

@receiver(post_save, sender=OrderItem)
def deduct_inventory(sender, instance, created, **kwargs):
    if created:
        # 1. Get the Menu Item for this order item
        menu_item = instance.menu_item
        
        # 2. Find all recipe ingredients (BOM) linked to this menu item
        recipe = RecipeIngredient.objects.filter(menu_item=menu_item)
        
        for ingredient in recipe:
            # 3. Calculate total deduction (quantity ordered * quantity per recipe)
            total_deduction = instance.quantity * ingredient.quantity_required
            
            # 4. Deduct from RawMaterial stock
            raw_material = ingredient.raw_material
            raw_material.current_stock -= total_deduction
            raw_material.save()
            
            print(f"DEBUG: Deducted {total_deduction} {raw_material.unit.short_code} of {raw_material.name}")
