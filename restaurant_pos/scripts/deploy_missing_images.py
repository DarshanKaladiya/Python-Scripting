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
    'S001': 'paneer_tikka_s001_1775832510828.png',
    'S002': 'chicken_tikka_s002_1775832527164.png',
    'S003': 'veg_crispy_s003_1775832543316.png',
    'M005': 'mutton_biryani_m005_1775832558776.png',
    'M006': 'jeera_rice_m006_1775832574495.png',
    'B011': 'butter_naan_b011_1775832597054.png',
    'B012': 'garlic_naan_b012_1775832613007.png',
    'B013': 'laccha_paratha_b013_1775832632774.png',
    'B014': 'tandoori_roti_b014_1775832647860.png',
    'D001': 'cold_coffee_d001_1775832665452.png',
    'D003': 'fresh_lime_soda_d003_1775832681152.png',
    'D004': 'virgin_mojito_d004_1775832698502.png',
    'D005': 'oreo_shake_d005_1775832715589.png',
    'D006': 'blue_lagoon_d006_1775832737082.png',
    'D007': 'sweet_lassi_d007_1775832753925.png',
}

def deploy_batch(batch_mapping):
    for sku, filename in batch_mapping.items():
        src_path = os.path.join(src_dir, filename)
        if os.path.exists(src_path):
            # Target filename in media
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
    print("Starting deployment of batch 1 images...")
    deploy_batch(mapping)
    print("Deployment completed.")
