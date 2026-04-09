import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from menu.models import Category, MenuItem, RecipeIngredient
from inventory.models import Unit, RawMaterial

def seed():
    # 1. Categories
    coffee_cat, _ = Category.objects.get_or_create(name='Coffee', defaults={'order': 12, 'color_code': '#4b2c20'})
    tea_cat, _ = Category.objects.get_or_create(name='Tea', defaults={'order': 13, 'color_code': '#166534'})

    # 1. Units
    kg = Unit.objects.get(short_code='kg')
    ltr = Unit.objects.get(short_code='ltr')
    gm = Unit.objects.get(short_code='g')

    # 2. Raw Materials
    milk, _ = RawMaterial.objects.get_or_create(name='Fresh Milk', sku='RM006', defaults={'current_stock': 30, 'reorder_level': 5, 'unit': ltr})
    sugar, _ = RawMaterial.objects.get_or_create(name='Sugar', sku='RM007', defaults={'current_stock': 20, 'reorder_level': 2, 'unit': kg})
    coffee_beans, _ = RawMaterial.objects.get_or_create(name='Roasted Coffee Beans', sku='RM020', defaults={'current_stock': 10, 'reorder_level': 2, 'unit': kg})
    tea_leaves, _ = RawMaterial.objects.get_or_create(name='Darjeeling Tea Leaves', sku='RM021', defaults={'current_stock': 10, 'reorder_level': 2, 'unit': kg})
    ginger, _ = RawMaterial.objects.get_or_create(name='Fresh Ginger', sku='RM022', defaults={'current_stock': 5, 'reorder_level': 1, 'unit': kg})
    cardamom, _ = RawMaterial.objects.get_or_create(name='Cardamom', sku='RM023', defaults={'current_stock': 2, 'reorder_level': 0.5, 'unit': kg})
    spices = RawMaterial.objects.get(sku='RM017')

    def add_item(name, category, price, sku, item_type='veg', ingredients=None):
        item, created = MenuItem.objects.get_or_create(
            sku=sku,
            defaults={
                'name': name, 
                'category': category, 
                'base_price': price, 
                'item_type': item_type
            }
        )
        if ingredients:
            RecipeIngredient.objects.filter(menu_item=item).delete()
            for rm, qty in ingredients:
                RecipeIngredient.objects.create(menu_item=item, raw_material=rm, quantity_required=qty)
        return item

    # --- COFFEES ---
    add_item('Espresso Shot', coffee_cat, 120, 'CF001', 'veg', [(coffee_beans, 0.015)])
    add_item('Cappuccino', coffee_cat, 180, 'CF002', 'veg', [(coffee_beans, 0.015), (milk, 0.150)])
    add_item('Cafe Latte', coffee_cat, 190, 'CF003', 'veg', [(coffee_beans, 0.015), (milk, 0.200)])
    add_item('Americano', coffee_cat, 150, 'CF004', 'veg', [(coffee_beans, 0.020)])
    add_item('Caramel Macchiato', coffee_cat, 220, 'CF005', 'veg', [(coffee_beans, 0.015), (milk, 0.150), (sugar, 0.020)])
    add_item('Hazelnut Latte', coffee_cat, 210, 'CF006', 'veg', [(coffee_beans, 0.015), (milk, 0.200)])

    # --- TEAS (Indian Style) ---
    add_item('Ginger Tea', tea_cat, 80, 'TE001', 'veg', [(tea_leaves, 0.010), (milk, 0.100), (ginger, 0.005)])
    add_item('Cardamom Tea', tea_cat, 80, 'TE002', 'veg', [(tea_leaves, 0.010), (milk, 0.100), (cardamom, 0.002)])
    add_item('Cutting Chai', tea_cat, 60, 'TE003', 'veg', [(tea_leaves, 0.008), (milk, 0.080)])
    add_item('Adrak Wali Chai', tea_cat, 90, 'TE004', 'veg', [(tea_leaves, 0.010), (milk, 0.100), (ginger, 0.010)])
    add_item('Masala Chai Premium', tea_cat, 100, 'TE005', 'veg', [(tea_leaves, 0.010), (milk, 0.100), (spices, 10)])

    print("Success: 11 New Coffee & Tea Items Seeded!")

if __name__ == '__main__':
    seed()
