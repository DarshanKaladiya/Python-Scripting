import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from menu.models import Category, MenuItem, RecipeIngredient
from inventory.models import Unit, RawMaterial

def seed():
    # 1. Units
    kg = Unit.objects.get(short_code='kg')
    ltr = Unit.objects.get(short_code='ltr')
    gm = Unit.objects.get(short_code='g')
    pc = Unit.objects.get(short_code='pc')

    # 2. Existing Raw Materials
    paneer = RawMaterial.objects.get(sku='RM001')
    chicken = RawMaterial.objects.get(sku='RM003')
    butter = RawMaterial.objects.get(sku='RM004')
    cream = RawMaterial.objects.get(sku='RM005')
    milk = RawMaterial.objects.get(sku='RM006')
    sugar = RawMaterial.objects.get(sku='RM007')
    potato = RawMaterial.objects.get(sku='RM009')
    flour = RawMaterial.objects.get(sku='RM010')
    cheese = RawMaterial.objects.get(sku='RM016')
    spices = RawMaterial.objects.get(sku='RM017')

    # 3. New Raw Materials
    pasta, _ = RawMaterial.objects.get_or_create(name='Penne Pasta', sku='RM030', defaults={'unit': kg, 'current_stock': 20, 'reorder_level': 5})
    olives, _ = RawMaterial.objects.get_or_create(name='Black Olives', sku='RM031', defaults={'unit': kg, 'current_stock': 5, 'reorder_level': 1})
    quinoa, _ = RawMaterial.objects.get_or_create(name='Quinoa', sku='RM032', defaults={'unit': kg, 'current_stock': 10, 'reorder_level': 2})
    chocolate, _ = RawMaterial.objects.get_or_create(name='Dark Chocolate', sku='RM033', defaults={'unit': kg, 'current_stock': 10, 'reorder_level': 2})
    mango, _ = RawMaterial.objects.get_or_create(name='Mango Pulp', sku='RM034', defaults={'unit': ltr, 'current_stock': 20, 'reorder_level': 5})
    pav, _ = RawMaterial.objects.get_or_create(name='Pav (Bread)', sku='RM035', defaults={'unit': pc, 'current_stock': 200, 'reorder_level': 50})

    # 4. Categories
    cont_pasta, _ = Category.objects.get_or_create(name='Continental & Pasta', defaults={'order': 14, 'color_code': '#6366f1'})
    healthy, _ = Category.objects.get_or_create(name='Salads & Healthy', defaults={'order': 15, 'color_code': '#10b981'})
    ind_spec, _ = Category.objects.get_or_create(name='Indian Specials', defaults={'order': 16, 'color_code': '#f59e0b'})
    
    # Get existing categories for expansion
    desserts = Category.objects.get(name='Desserts')
    drinks = Category.objects.get(name='Drinks')

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

    # --- CONTINENTAL & PASTA ---
    add_item('Penne Arrabbiata', cont_pasta, 320, 'CP001', 'veg', [(pasta, 0.150), (spices, 10)])
    add_item('Creamy Mushroom Alfredo', cont_pasta, 380, 'CP002', 'veg', [(pasta, 0.150), (cream, 0.050), (cheese, 0.030)])
    add_item('BBQ Chicken Wings', cont_pasta, 420, 'CP003', 'non_veg', [(chicken, 0.300)])
    add_item('Classic Loaded Nachos', cont_pasta, 250, 'CP004', 'veg', [(cheese, 0.050)])

    # --- SALADS & HEALTHY ---
    add_item('Classic Greek Salad', healthy, 280, 'HS001', 'veg', [(olives, 0.030), (cheese, 0.030)])
    add_item('Grilled Chicken Quinoa Bowl', healthy, 450, 'HS002', 'non_veg', [(quinoa, 0.100), (chicken, 0.150)])

    # --- INDIAN SPECIALS ---
    add_item('Amritsari Chole Bhature', ind_spec, 180, 'IS001', 'veg', [(flour, 0.150)])
    add_item('Tandoori Mixed Platter', ind_spec, 650, 'IS002', 'non_veg', [(chicken, 0.200), (paneer, 0.100)])

    # --- PAV BHAJI SERIES ---
    add_item('Butter Pav Bhaji', ind_spec, 150, 'PB001', 'veg', [(potato, 0.200), (butter, 0.030), (pav, 2)])
    add_item('Cheese Pav Bhaji', ind_spec, 190, 'PB002', 'veg', [(potato, 0.200), (butter, 0.020), (cheese, 0.030), (pav, 2)])
    add_item('Paneer Pav Bhaji', ind_spec, 210, 'PB003', 'veg', [(potato, 0.200), (paneer, 0.050), (pav, 2)])
    add_item('Kada Pav Bhaji', ind_spec, 170, 'PB004', 'veg', [(potato, 0.150), (spices, 15), (pav, 2)])
    add_item('Jain Pav Bhaji', ind_spec, 160, 'PB005', 'veg', [(spices, 15), (pav, 2)]) # Jain uses raw banana instead of potato (not explicitly in RM yet, but spiced)

    # --- DESSERTS & SHAKES ---
    add_item('Death by Chocolate', desserts, 280, 'DE010', 'veg', [(chocolate, 0.100), (cream, 0.030)])
    add_item('Fresh Mango Mastani', drinks, 220, 'D020', 'veg', [(mango, 0.150), (milk, 0.150), (sugar, 0.030)])

    print("Success: 15 New Gourmet Dishes & Inventory Mapped!")

if __name__ == '__main__':
    seed()
