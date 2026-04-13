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
    mutton = RawMaterial.objects.get(sku='RM012')
    fish = RawMaterial.objects.get(sku='RM013')
    lentils = RawMaterial.objects.get(sku='RM015')
    spices = RawMaterial.objects.get(sku='RM017')

    # 3. New Raw Materials for V4
    soya, _ = RawMaterial.objects.get_or_create(name='Soya Chaap Chunks', sku='RM050', defaults={'unit': kg, 'current_stock': 10, 'reorder_level': 2})
    methi, _ = RawMaterial.objects.get_or_create(name='Fresh Methi (Fenugreek)', sku='RM051', defaults={'unit': kg, 'current_stock': 5, 'reorder_level': 1})
    mutton_keema, _ = RawMaterial.objects.get_or_create(name='Ground Mutton (Keema)', sku='RM052', defaults={'unit': kg, 'current_stock': 10, 'reorder_level': 2})
    raw_mango, _ = RawMaterial.objects.get_or_create(name='Raw Mango', sku='RM053', defaults={'unit': kg, 'current_stock': 5, 'reorder_level': 1})
    rose_syrup, _ = RawMaterial.objects.get_or_create(name='Rose Syrup', sku='RM054', defaults={'unit': ltr, 'current_stock': 5, 'reorder_level': 1})

    # 4. Categories
    starters = Category.objects.get(name='Starters')
    drinks = Category.objects.get(name='Drinks')
    ind_veg = Category.objects.get(name='Indian Veg Mains')
    ind_nonveg = Category.objects.get(name='Indian Non-Veg')

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

    # --- STARTERS (Indian Style) ---
    add_item('Soya Chaap Tikka', starters, 220, 'S010', 'veg', [(soya, 0.200), (spices, 10)])
    add_item('Hara Bhara Kebab', starters, 190, 'S011', 'veg', [(spices, 15)])
    add_item('Fish Amritsari', starters, 380, 'S012', 'non_veg', [(fish, 0.200), (spices, 10)])
    add_item('Murg Malai Kebab', starters, 350, 'S013', 'non_veg', [(chicken, 0.200), (cream, 0.050)])

    # --- MAIN COURSE (Indian Veg) ---
    add_item('Paneer Lababdar', ind_veg, 390, 'IV010', 'veg', [(paneer, 0.200), (cream, 0.040)])
    add_item('Methi Matar Malai', ind_veg, 350, 'IV011', 'veg', [(methi, 0.100), (cream, 0.050)])
    add_item('Dhaba Style Dal Tadka', ind_veg, 180, 'IV012', 'veg', [(lentils, 0.150), (butter, 0.020)])

    # --- MAIN COURSE (Indian Non-Veg) ---
    add_item('Mutton Bhuna Gosht', ind_nonveg, 550, 'INV010', 'non_veg', [(mutton, 0.300), (spices, 20)])
    add_item('Chicken Rara', ind_nonveg, 480, 'INV011', 'non_veg', [(chicken, 0.250), (mutton_keema, 0.050), (spices, 20)])

    # --- DRINKS (Indian Style) ---
    add_item('Aam Panna', drinks, 90, 'D010', 'veg', [(raw_mango, 0.100), (sugar, 0.020)])
    add_item('Rose Falooda Shake', drinks, 180, 'D011', 'veg', [(rose_syrup, 0.050), (milk, 0.200), (sugar, 0.020)])
    add_item('Shikanji (Indian Lemonade)', drinks, 70, 'D012', 'veg', [(sugar, 0.020), (spices, 5)])
    add_item('Nawabi Thandai', drinks, 120, 'D013', 'veg', [(milk, 0.200), (sugar, 0.030), (spices, 5)])

    print("Success: 13 Authentic Indian Dishes & Inventory Mapped!")

if __name__ == '__main__':
    seed()
