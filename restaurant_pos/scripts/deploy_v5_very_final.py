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

# Mapping of SKU to filename
mapping = {
    'DE014': 'shahi_tukda_de014_final_attempt_1776076361688.png',
    'DE015': 'phirni_de015_final_attempt_1776076382569.png',
    'DE016': 'mishti_doi_de016_final_attempt_1776076403832.png',
    'DE017': 'paan_ice_cream_de017_final_attempt_1776076422903.png',
}

def deploy_images(image_mapping):
    for sku, filename in image_mapping.items():
        src_path = os.path.join(src_dir, filename)
        if os.path.exists(src_path):
            clean_name = f"{sku.lower()}.png"
            target_path = os.path.join(dest_dir, clean_name)
            shutil.copy2(src_path, target_path)
            print(f"Copied {filename} to {clean_name}")
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
    print("Starting deployment of the VERY final 4 images...")
    deploy_images(mapping)
    print("Final deployment completed.")
