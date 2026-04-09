import os
import shutil
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from menu.models import MenuItem

# Source directory (Artifacts)
src_dir = r"C:\Users\DARSHAN\.gemini\antigravity\brain\e5790e98-7424-432b-8143-01e2f10fe9a9"
# Destination directory (Media)
dest_dir = r"d:\Intership\Python Automation\restaurant_pos\media\menu_items"

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Mapping of SKU to filename
mapping = {
    'B001': 'veg_maharaja_burger_hero_1775721677971.png',
    'B002': 'crispy_chicken_burger_1775721827629.png',
    'B003': 'aloo_tikki_burger_1775721848914.png',
    'B004': 'paneer_tikka_roll_1775721865251.png',
    'B005': 'chicken_egg_wrap_1775721882596.png',
    'P001': 'margherita_pizza_premium_1775721902916.png',
    'P002': 'paneer_tikka_pizza_premium_1775721917733.png',
    'P003': 'chicken_supreme_pizza_premium_1775721933514.png',
    'P004': 'farmhouse_veggie_pizza_premium_1775721947893.png',
    'P005': 'spicy_chicken_pizza_premium_1775721963397.png',
    'C001': 'gobi_manchurian_chinese_premium_1775721983826.png',
    'C002': 'veg_manchurian_chinese_premium_1775722000556.png',
    'C003': 'veg_hakka_noodles_chinese_premium_1775722014792.png',
    'C004': 'chicken_fried_rice_chinese_premium_1775722028418.png',
    'C005': 'chilli_paneer_chinese_premium_1775722043576.png',
    'C006': 'chicken_lollipop_chinese_premium_1775722060951.png',
    'SI001': 'masala_dosa_south_indian_premium_1775722080480.png',
}

for sku, filename in mapping.items():
    src_path = os.path.join(src_dir, filename)
    if os.path.exists(src_path):
        # Target filename in media (keeping it clean)
        clean_name = f"{sku}.png"
        target_path = os.path.join(dest_dir, clean_name)
        
        # Copy file
        shutil.copy2(src_path, target_path)
        
        # Update Database
        try:
            item = MenuItem.objects.get(sku=sku)
            item.image = f"menu_items/{clean_name}"
            item.save()
            print(f"Updated {item.name} ({sku}) with {clean_name}")
        except MenuItem.DoesNotExist:
            print(f"MenuItem with SKU {sku} not found.")
    else:
        print(f"Source file {filename} not found.")

print("Deployment of Batch 1 images completed.")
