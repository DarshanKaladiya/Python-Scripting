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
    'D002': 'masala_chai_d002_1775875704861.png',
    'DE001': 'gulab_jamun_de001_v2_1775875722290.png',
    'D008': 'masala_buttermilk_d008_v2_1775875738861.png',
    'DE002': 'gajar_halwa_de002_v2_1775875757361.png',
    'DE003': 'sizzling_brownie_de003_v2_1775875776012.png',
    'DE004': 'kulfi_falooda_de004_v2_1775875792832.png',
    'CF001': 'espresso_shot_cf001_v2_1775875815568.png',
    'CF002': 'cappuccino_cf002_v2_1775875830819.png',
    'CF003': 'cafe_latte_cf003_v2_1775875853015.png',
    'CF004': 'americano_cf004_v2_1775875873278.png',
    'CF005': 'caramel_macchiato_cf005_v2_1775875889929.png',
    'CF006': 'hazelnut_latte_cf006_v2_1775875905993.png',
    'TE001': 'ginger_tea_te001_v2_1775875923085.png',
    'TE002': 'cardamom_tea_te002_v2_1775875939297.png',
    'TE003': 'cutting_chai_te003_v2_1775875956798.png',
    'TE004': 'adrak_chai_te004_v2_1775875975059.png',
    'TE005': 'masala_chai_premium_te005_v2_1775875990572.png',
}

def deploy_batch(batch_mapping):
    for sku, filename in batch_mapping.items():
        src_path = os.path.join(src_dir, filename)
        if os.path.exists(src_path):
            # Target filename in media (keeping it clean)
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
    print("Starting deployment of final batch images...")
    deploy_batch(mapping)
    print("Deployment completed.")
