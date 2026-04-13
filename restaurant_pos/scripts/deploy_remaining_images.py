import os
import shutil
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from menu.models import MenuItem

# Source directory (Artifacts)
src_dir = r"C:\Users\DARSHAN\.gemini\antigravity\brain\62c9c088-2eca-4e00-9d97-6ec433f8e24c"
# Destination directory (Media)
dest_dir = r"d:\Intership\Python Automation\restaurant_pos\media\menu_items"

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Mapping of SKU to filename
mapping = {
    'IV001': 'kadai_paneer_iv001_1775811517221.png',
    'IV002': 'dal_makhani_iv002_1775811532571.png',
    'IV003': 'mix_veg_masala_iv003_1775811549275.png',
    'IV004': 'paneer_butter_masala_iv004_1775811571973.png',
    'IV005': 'malai_kofta_iv005_1775811587146.png',
    'INV001': 'mutton_rogan_josh_inv001_1775811662391.png',
    'INV002': 'chicken_tikka_masala_inv002_1775811607745.png',
    'INV003': 'goan_fish_curry_inv003_1775811621758.png',
    'INV004': 'butter_chicken_inv004_m001_1775811639826.png',
    'M001': 'butter_chicken_inv004_m001_1775811639826.png',
    'M002': 'paneer_butter_masala_m002_alt_1775811690536.png',
    'SI002': 'idli_sambhar_si002_1775811739602.png',
    'SI003': 'medu_vada_si003_1775811758518.png',
    'SI004': 'paneer_dosa_si004_1775811775535.png',
    'SI005': 'onion_uttapam_si005_1775811791087.png',
    'M003': 'veg_dum_biryani_m003_1775811812524.png',
}

def deploy_batch(batch_mapping):
    for sku, filename in batch_mapping.items():
        src_path = os.path.join(src_dir, filename)
        if os.path.exists(src_path):
            # Target filename in media (keeping it clean)
            clean_name = f"{sku}.png"
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
    print("Starting deployment of newly generated images...")
    deploy_batch(mapping)
    print("Deployment completed.")
