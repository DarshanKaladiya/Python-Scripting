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
    milk = RawMaterial.objects.get(sku='RM006')
    rice = RawMaterial.objects.get(sku='RM008')
    potato = RawMaterial.objects.get(sku='RM009')
    flour = RawMaterial.objects.get(sku='RM010')
    fish = RawMaterial.objects.get(sku='RM013')
    cheese = RawMaterial.objects.get(sku='RM016')
    spices = RawMaterial.objects.get(sku='RM017')
    olives = RawMaterial.objects.get(sku='RM031')

    # 3. New Raw Materials for V3
    egg, _ = RawMaterial.objects.get_or_create(name='Eggs', sku='RM040', defaults={'unit': pc, 'current_stock': 120, 'reorder_level': 24})
    rava, _ = RawMaterial.objects.get_or_create(name='Semolina (Rava)', sku='RM041', defaults={'unit': kg, 'current_stock': 15, 'reorder_level': 2})
    zucchini, _ = RawMaterial.objects.get_or_create(name='Fresh Zucchini', sku='RM042', defaults={'unit': kg, 'current_stock': 5, 'reorder_level': 1})
    black_beans, _ = RawMaterial.objects.get_or_create(name='Black Beans', sku='RM043', defaults={'unit': kg, 'current_stock': 10, 'reorder_level': 2})

    # 4. Categories
    starters = Category.objects.get(name='Starters')
    burgers = Category.objects.get(name='Burgers & Wraps')
    pizzas = Category.objects.get(name='Pizzas')
    dosa = Category.objects.get(name='South Indian')
    mains = Category.objects.get(name='Main Course')
    ind_veg = Category.objects.get(name='Indian Veg Mains')

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

    # --- PIZZA EXPANSION ---
    add_item('Four Cheese Pizza', pizzas, 480, 'P006', 'veg', [(cheese, 0.150), (milk, 0.050)])
    add_item('Garden Fresh Pizza', pizzas, 420, 'P007', 'veg', [(cheese, 0.100), (zucchini, 0.050), (olives, 0.020)])
    add_item('Tandoori Chicken Pizza', pizzas, 520, 'P008', 'non_veg', [(cheese, 0.100), (chicken, 0.150), (spices, 10)])

    # --- BURGER EXPANSION ---
    add_item('Mexican Spicy Bean Burger', burgers, 220, 'B006', 'veg', [(black_beans, 0.080), (spices, 5)])
    add_item('Double Cheese Mushroom Burger', burgers, 260, 'B007', 'veg', [(cheese, 0.060), (potato, 0.050)])
    add_item('Crispy Fish Fillet Burger', burgers, 310, 'B008', 'non_veg', [(fish, 0.120), (flour, 0.030)])

    # --- DOSA EXPANSION ---
    add_item('Schezwan Cheese Dosa', dosa, 180, 'SI006', 'veg', [(cheese, 0.040), (spices, 10)])
    add_item('Paper Plain Dosa (Jumbo)', dosa, 120, 'SI007', 'veg', [(rice, 0.100)])
    add_item('Rava Onion Masala Dosa', dosa, 160, 'SI008', 'veg', [(rava, 0.100), (potato, 0.050)])

    # --- INDIAN SPECIALTIES ---
    add_item('Hyderabadi Egg Biryani', mains, 320, 'M007', 'egg', [(rice, 0.200), (egg, 2), (spices, 15)])
    add_item('Kashmiri Dum Aloo', ind_veg, 280, 'IV006', 'veg', [(potato, 0.250), (spices, 20)])
    add_item('Malai Seekh Kebab', starters, 380, 'S004', 'non_veg', [(chicken, 0.250), (milk, 0.050)])

    print("Success: 12 Diversified Menu Items & Inventory Mapped!")

if __name__ == '__main__':
    seed()
