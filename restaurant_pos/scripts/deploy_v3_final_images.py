import os
import shutil
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from menu.models import MenuItem

# Source directory (Artifacts)
src_dir = r"C:\Users\DARSHAN\.gemini\antigravity\brain\e889f9e8-dd4f-4a1a-ab01-7186300ed70a"
# Destination directory (Media)
dest_dir = r"d:\Intership\Python Automation\restaurant_pos\media\menu_items"

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Mapping of SKU to filename
mapping = {
    'P008': 'tandoori_chicken_pizza_p008_v2_1775992045504.png',
    'B006': 'mexican_bean_burger_b006_v2_1775992062103.png',
    'B007': 'double_cheese_mushroom_burger_b007_v2_1775992079926.png',
    'B008': 'fish_fillet_burger_b008_v2_1775992094050.png',
    'SI006': 'schezwan_cheese_dosa_si006_v2_1775992111014.png',
    'SI007': 'paper_dosa_si007_v2_1775992128654.png',
    'SI008': 'rava_masala_dosa_si008_v2_1775992144924.png',
    'M007': 'egg_biryani_m007_v2_1775992160711.png',
    'IV006': 'dum_aloo_iv006_v2_1775992176987.png',
    'S004': 'malai_seekh_kebab_s004_v2_1775992191632.png',
}

def deploy_images(image_mapping):
    for sku, filename in image_mapping.items():
        src_path = os.path.join(src_dir, filename)
        if os.path.exists(src_path):
            clean_name = f"{sku.lower()}.png"
            target_path = os.path.join(dest_dir, clean_name)
            
            # Copy file
            shutil.copy2(src_path, target_path)
            print(f"Copied {filename} to {clean_name}")
            
            # Update Database
            try:
                item = MenuItem.objects.get(sku=sku)
                item.image = f"menu_items/{clean_name}"
                item.save()
                print(f"Updated {item.name} ({sku}) in DB")
            except MenuItem.DoesNotExist:
                print(f"MenuItem with SKU {sku} not found.")
        else:
            print(f"Source file {filename} not found at {src_path}")

if __name__ == '__main__':
    print("Starting final deployment of diversified batch images...")
    deploy_images(mapping)
    print("Deployment completed.")
