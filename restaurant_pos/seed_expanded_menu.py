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

    # 2. Raw Materials (New & Existing)
    # Existing
    paneer, _ = RawMaterial.objects.get_or_create(name='Paneer', sku='RM001', unit=kg, defaults={'current_stock': 50, 'reorder_level': 5})
    chicken, _ = RawMaterial.objects.get_or_create(name='Fresh Chicken', sku='RM003', unit=kg, defaults={'current_stock': 100, 'reorder_level': 10})
    butter, _ = RawMaterial.objects.get_or_create(name='Butter', sku='RM004', unit=kg, defaults={'current_stock': 20, 'reorder_level': 2})
    cream, _ = RawMaterial.objects.get_or_create(name='Cooking Cream', sku='RM005', unit=ltr, defaults={'current_stock': 10, 'reorder_level': 1})
    milk, _ = RawMaterial.objects.get_or_create(name='Fresh Milk', sku='RM006', unit=ltr, defaults={'current_stock': 30, 'reorder_level': 5})
    sugar, _ = RawMaterial.objects.get_or_create(name='Sugar', sku='RM007', unit=kg, defaults={'current_stock': 20, 'reorder_level': 2})
    rice, _ = RawMaterial.objects.get_or_create(name='Basmati Rice', sku='RM008', unit=kg, defaults={'current_stock': 100, 'reorder_level': 10})

    # New Raw Materials
    potato, _ = RawMaterial.objects.get_or_create(name='Potato', sku='RM009', unit=kg, defaults={'current_stock': 100, 'reorder_level': 15})
    flour, _ = RawMaterial.objects.get_or_create(name='All-purpose Flour', sku='RM010', unit=kg, defaults={'current_stock': 50, 'reorder_level': 5})
    yeast, _ = RawMaterial.objects.get_or_create(name='Yeast', sku='RM011', unit=gm, defaults={'current_stock': 500, 'reorder_level': 50})
    mutton, _ = RawMaterial.objects.get_or_create(name='Mutton', sku='RM012', unit=kg, defaults={'current_stock': 30, 'reorder_level': 5})
    fish, _ = RawMaterial.objects.get_or_create(name='Fish', sku='RM013', unit=kg, defaults={'current_stock': 20, 'reorder_level': 5})
    noodles, _ = RawMaterial.objects.get_or_create(name='Noodles', sku='RM014', unit=kg, defaults={'current_stock': 20, 'reorder_level': 5})
    dal, _ = RawMaterial.objects.get_or_create(name='Lentils (Dal)', sku='RM015', unit=kg, defaults={'current_stock': 50, 'reorder_level': 10})
    cheese, _ = RawMaterial.objects.get_or_create(name='Mozzarella Cheese', sku='RM016', unit=kg, defaults={'current_stock': 25, 'reorder_level': 5})
    spices, _ = RawMaterial.objects.get_or_create(name='Mixed Spices', sku='RM017', unit=gm, defaults={'current_stock': 2000, 'reorder_level': 200})

    # 3. Categories
    # Existing
    starters, _ = Category.objects.get_or_create(name='Starters', defaults={'order': 1, 'color_code': '#f97316'})
    mains, _ = Category.objects.get_or_create(name='Main Course', defaults={'order': 2, 'color_code': '#8b5cf6'})
    drinks, _ = Category.objects.get_or_create(name='Drinks', defaults={'order': 9, 'color_code': '#06b6d4'})
    desserts, _ = Category.objects.get_or_create(name='Desserts', defaults={'order': 10, 'color_code': '#ec4899'})

    # New Categories
    burgers, _ = Category.objects.get_or_create(name='Burgers & Wraps', defaults={'order': 3, 'color_code': '#f59e0b'})
    pizzas, _ = Category.objects.get_or_create(name='Pizzas', defaults={'order': 4, 'color_code': '#ef4444'})
    chinese, _ = Category.objects.get_or_create(name='Chinese', defaults={'order': 5, 'color_code': '#b91c1c'})
    south_indian, _ = Category.objects.get_or_create(name='South Indian', defaults={'order': 6, 'color_code': '#10b981'})
    indian_veg, _ = Category.objects.get_or_create(name='Indian Veg Mains', defaults={'order': 7, 'color_code': '#84cc16'})
    indian_non_veg, _ = Category.objects.get_or_create(name='Indian Non-Veg', defaults={'order': 8, 'color_code': '#7f1d1d'})
    breads, _ = Category.objects.get_or_create(name='Indian Breads', defaults={'order': 11, 'color_code': '#d97706'})

    # 4. Helper Function
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
        if not created:
            item.name = name
            item.category = category
            item.base_price = price
            item.item_type = item_type
            item.save()

        if ingredients:
            RecipeIngredient.objects.filter(menu_item=item).delete()
            for rm, qty in ingredients:
                RecipeIngredient.objects.create(menu_item=item, raw_material=rm, quantity_required=qty)
        return item

    # --- BURGERS & WRAPS ---
    add_item('Veg Maharaja Burger', burgers, 220, 'B001', 'veg', [(potato, 0.150), (cheese, 0.030)])
    add_item('Crispy Chicken Burger', burgers, 280, 'B002', 'non_veg', [(chicken, 0.200), (cheese, 0.030)])
    add_item('Aloo Tikki Burger', burgers, 120, 'B003', 'veg', [(potato, 0.100)])
    add_item('Paneer Tikka Roll', burgers, 180, 'B004', 'veg', [(paneer, 0.100), (flour, 0.080)])
    add_item('Chicken Egg Wrap', burgers, 210, 'B005', 'egg', [(chicken, 0.100), (flour, 0.080)])

    # --- PIZZAS ---
    add_item('Margherita Pizza', pizzas, 350, 'P001', 'veg', [(flour, 0.200), (cheese, 0.100)])
    add_item('Paneer Tikka Pizza', pizzas, 450, 'P002', 'veg', [(flour, 0.200), (cheese, 0.120), (paneer, 0.100)])
    add_item('Chicken Supreme Pizza', pizzas, 550, 'P003', 'non_veg', [(flour, 0.200), (cheese, 0.120), (chicken, 0.150)])
    add_item('Farmhouse Veggie Pizza', pizzas, 420, 'P004', 'veg', [(flour, 0.200), (cheese, 0.100)])
    add_item('Spicy Chicken Pizza', pizzas, 480, 'P005', 'non_veg', [(flour, 0.200), (cheese, 0.120), (chicken, 0.100)])

    # --- CHINESE ---
    add_item('Gobi Manchurian Dry', chinese, 180, 'C001', 'veg', [(flour, 0.050)])
    add_item('Veg Manchurian Gravy', chinese, 220, 'C002', 'veg', [(flour, 0.050)])
    add_item('Veg Hakka Noodles', chinese, 200, 'C003', 'veg', [(noodles, 0.200)])
    add_item('Chicken Fried Rice', chinese, 250, 'C004', 'non_veg', [(rice, 0.200), (chicken, 0.100)])
    add_item('Chilli Paneer', chinese, 240, 'C005', 'veg', [(paneer, 0.150), (flour, 0.030)])
    add_item('Chicken Lollipop', chinese, 320, 'C006', 'non_veg', [(chicken, 0.250)])

    # --- SOUTH INDIAN ---
    add_item('Masala Dosa', south_indian, 120, 'SI001', 'veg', [(rice, 0.100), (potato, 0.100)])
    add_item('Idli Sambhar', south_indian, 80, 'SI002', 'veg', [(rice, 0.080), (dal, 0.040)])
    add_item('Medu Vada', south_indian, 90, 'SI003', 'veg', [(dal, 0.100)])
    add_item('Paneer Dosa', south_indian, 160, 'SI004', 'veg', [(rice, 0.100), (paneer, 0.050)])
    add_item('Onion Uttapam', south_indian, 110, 'SI005', 'veg', [(rice, 0.100)])

    # --- INDIAN VEG MAINS ---
    add_item('Kadai Paneer', indian_veg, 320, 'IV001', 'veg', [(paneer, 0.200), (butter, 0.020)])
    add_item('Dal Makhani', indian_veg, 280, 'IV002', 'veg', [(dal, 0.150), (butter, 0.050), (cream, 0.050)])
    add_item('Mix Veg Masala', indian_veg, 240, 'IV003', 'veg', [(potato, 0.100)])
    add_item('Paneer Butter Masala', indian_veg, 340, 'IV004', 'veg', [(paneer, 0.200), (butter, 0.040), (cream, 0.030)])
    add_item('Malai Kofta', indian_veg, 360, 'IV005', 'veg', [(paneer, 0.100), (potato, 0.100), (cream, 0.050)])

    # --- INDIAN NON-VEG MAINS ---
    add_item('Mutton Rogan Josh', indian_non_veg, 550, 'INV001', 'non_veg', [(mutton, 0.300), (spices, 30)])
    add_item('Chicken Tikka Masala', indian_non_veg, 420, 'INV002', 'non_veg', [(chicken, 0.250), (butter, 0.030), (cream, 0.030)])
    add_item('Goan Fish Curry', indian_non_veg, 480, 'INV003', 'non_veg', [(fish, 0.250), (milk, 0.100)])
    add_item('Butter Chicken', indian_non_veg, 450, 'INV004', 'non_veg', [(chicken, 0.300), (butter, 0.050), (cream, 0.050)])

    # --- RICE & BIRYANI ---
    add_item('Veg Dum Biryani', mains, 280, 'M003', 'veg', [(rice, 0.200), (potato, 0.050)]) # Re-using M003
    add_item('Chicken Biryani', mains, 350, 'M004', 'non_veg', [(rice, 0.200), (chicken, 0.200)]) # Re-using M004
    add_item('Mutton Dum Biryani', mains, 480, 'M005', 'non_veg', [(rice, 0.200), (mutton, 0.200)])
    add_item('Jeera Rice', mains, 150, 'M006', 'veg', [(rice, 0.200)])

    # --- BREADS ---
    add_item('Butter Naan', breads, 50, 'B011', 'veg', [(flour, 0.100), (butter, 0.020)])
    add_item('Garlic Naan', breads, 65, 'B012', 'veg', [(flour, 0.100), (butter, 0.020)])
    add_item('Laccha Paratha', breads, 60, 'B013', 'veg', [(flour, 0.120), (butter, 0.030)])
    add_item('Tandoori Roti', breads, 30, 'B014', 'veg', [(flour, 0.080)])

    # --- BEVERAGES ---
    add_item('Virgin Mojito', drinks, 150, 'D004', 'veg', [(sugar, 0.030)])
    add_item('Oreo Shake', drinks, 180, 'D005', 'veg', [(milk, 0.250), (sugar, 0.020)])
    add_item('Blue Lagoon', drinks, 160, 'D006', 'veg', [(sugar, 0.030)])
    add_item('Sweet Lassi', drinks, 90, 'D007', 'veg', [(milk, 0.200), (sugar, 0.040)])
    add_item('Masala Buttermilk', drinks, 60, 'D008', 'veg', [(milk, 0.200)])

    # --- DESSERTS ---
    add_item('Gajar Ka Halwa', desserts, 140, 'DE002', 'veg', [(sugar, 0.050), (milk, 0.100)])
    add_item('Sizzling Brownie', desserts, 250, 'DE003', 'veg', [(sugar, 0.030), (milk, 0.050)])
    add_item('Kulfi Falooda', desserts, 180, 'DE004', 'veg', [(milk, 0.150), (sugar, 0.040)])

    print("Success: 40+ Premium Menu Items & Inventory Seeded!")

if __name__ == '__main__':
    seed()
