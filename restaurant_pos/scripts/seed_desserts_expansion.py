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
    milk = RawMaterial.objects.get(sku='RM006')
    sugar = RawMaterial.objects.get(sku='RM007')
    spices = RawMaterial.objects.get(sku='RM017')
    rice = RawMaterial.objects.get(sku='RM008')

    # 3. New Raw Materials for Desserts
    rabri, _ = RawMaterial.objects.get_or_create(name='Rabri / Condensed Milk', sku='RM060', defaults={'unit': ltr, 'current_stock': 10, 'reorder_level': 2})
    moong_dal, _ = RawMaterial.objects.get_or_create(name='Yellow Moong Dal', sku='RM061', defaults={'unit': kg, 'current_stock': 15, 'reorder_level': 3})
    saffron, _ = RawMaterial.objects.get_or_create(name='Saffron (Kesar)', sku='RM062', defaults={'unit': gm, 'current_stock': 100, 'reorder_level': 10})
    yogurt, _ = RawMaterial.objects.get_or_create(name='Fresh Yogurt (Dahi)', sku='RM063', defaults={'unit': kg, 'current_stock': 20, 'reorder_level': 5})

    # 4. Category
    desserts = Category.objects.get(name='Desserts')

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

    # --- NEW INDIAN DESSERTS ---
    add_item('Rasmalai', desserts, 120, 'DE011', 'veg', [(paneer, 0.050), (milk, 0.200), (saffron, 0.01)])
    add_item('Rabri with Malpua', desserts, 180, 'DE012', 'veg', [(rabri, 0.100), (milk, 0.100)])
    add_item('Moong Dal Halwa', desserts, 150, 'DE013', 'veg', [(moong_dal, 0.100), (sugar, 0.050)])
    add_item('Shahi Tukda', desserts, 160, 'DE014', 'veg', [(rabri, 0.100), (sugar, 0.020)])
    add_item('Kesari Phirni', desserts, 110, 'DE015', 'veg', [(rice, 0.050), (milk, 0.200), (saffron, 0.01)])
    add_item('Baked Mishti Doi', desserts, 130, 'DE016', 'veg', [(yogurt, 0.200), (sugar, 0.050)])
    add_item('Gourmet Paan Ice Cream', desserts, 140, 'DE017', 'veg', [(milk, 0.150), (sugar, 0.030)])

    print("Success: 7 Authentic Indian Desserts & Inventory Mapped!")

if __name__ == '__main__':
    seed()
