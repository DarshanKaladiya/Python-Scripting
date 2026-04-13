import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from menu.models import Category, MenuItem, RecipeIngredient
from inventory.models import Unit, RawMaterial, Supplier

def seed():
    # 1. Units
    kg, _ = Unit.objects.get_or_create(name='Kilogram', short_code='kg')
    ltr, _ = Unit.objects.get_or_create(name='Liter', short_code='ltr')
    pc, _ = Unit.objects.get_or_create(name='Piece', short_code='pc')
    gm, _ = Unit.objects.get_or_create(name='Gram', short_code='g')

    # 2. Raw Materials
    paneer, _ = RawMaterial.objects.get_or_create(name='Paneer', sku='RM001', unit=kg, defaults={'current_stock': 50, 'reorder_level': 5})
    chicken, _ = RawMaterial.objects.get_or_create(name='Fresh Chicken', sku='RM003', unit=kg, defaults={'current_stock': 100, 'reorder_level': 10})
    butter, _ = RawMaterial.objects.get_or_create(name='Butter', sku='RM004', unit=kg, defaults={'current_stock': 20, 'reorder_level': 2})
    cream, _ = RawMaterial.objects.get_or_create(name='Cooking Cream', sku='RM005', unit=ltr, defaults={'current_stock': 10, 'reorder_level': 1})
    milk, _ = RawMaterial.objects.get_or_create(name='Fresh Milk', sku='RM006', unit=ltr, defaults={'current_stock': 30, 'reorder_level': 5})
    sugar, _ = RawMaterial.objects.get_or_create(name='Sugar', sku='RM007', unit=kg, defaults={'current_stock': 20, 'reorder_level': 2})
    rice, _ = RawMaterial.objects.get_or_create(name='Basmati Rice', sku='RM008', unit=kg, defaults={'current_stock': 100, 'reorder_level': 10})
    
    # 3. Categories
    starters, _ = Category.objects.get_or_create(name='Starters', defaults={'order': 1, 'color_code': '#f97316'})
    mains, _ = Category.objects.get_or_create(name='Main Course', defaults={'order': 2, 'color_code': '#8b5cf6'})
    drinks, _ = Category.objects.get_or_create(name='Drinks', defaults={'order': 3, 'color_code': '#06b6d4'})
    desserts, _ = Category.objects.get_or_create(name='Desserts', defaults={'order': 4, 'color_code': '#ec4899'})

    # 4. Helper to create item + optional recipe
    def add_item(name, category, price, sku, item_type='veg', ingredients=None):
        item, _ = MenuItem.objects.get_or_create(
            name=name, 
            category=category, 
            sku=sku,
            defaults={'base_price': price, 'item_type': item_type}
        )
        if ingredients:
            for rm, qty in ingredients:
                RecipeIngredient.objects.get_or_create(menu_item=item, raw_material=rm, defaults={'quantity_required': qty})
        return item

    # --- STARTERS ---
    add_item('Paneer Tikka', starters, 250, 'S001', 'veg', [(paneer, 0.200)])
    add_item('Chicken Tikka', starters, 320, 'S002', 'non_veg', [(chicken, 0.250), (butter, 0.020)])
    add_item('Veg Crispy', starters, 180, 'S003', 'veg')

    # --- MAIN COURSE ---
    add_item('Butter Chicken', mains, 450, 'M001', 'non_veg', [(chicken, 0.300), (butter, 0.050), (cream, 0.050)])
    add_item('Paneer Butter Masala', mains, 380, 'M002', 'veg', [(paneer, 0.200), (butter, 0.040), (cream, 0.030)])
    add_item('Veg Biryani', mains, 280, 'M003', 'veg', [(rice, 0.200)])
    add_item('Chicken Biryani', mains, 350, 'M004', 'non_veg', [(rice, 0.200), (chicken, 0.200)])

    # --- DRINKS ---
    add_item('Cold Coffee', drinks, 150, 'D001', 'veg', [(milk, 0.250), (sugar, 0.020)])
    add_item('Masala Chai', drinks, 40, 'D002', 'veg', [(milk, 0.100), (sugar, 0.010)])
    add_item('Fresh Lime Soda', drinks, 80, 'D003', 'veg', [(sugar, 0.020)])

    # --- DESSERTS ---
    add_item('Gulab Jamun', desserts, 120, 'DE001', 'veg', [(sugar, 0.050)])

    print("Comprehensive Menu & Inventory Seeded Successfully!")

if __name__ == '__main__':
    seed()
