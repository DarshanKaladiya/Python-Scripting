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

# Mapping of SKU to filename (Confirmed successful ones)
mapping = {
    'INV010': 'bhuna_gosht_inv010_v2_1776072089559.png',
    'INV011': 'chicken_rara_inv011_v3_1776076180219.png',
    'D010': 'aam_panna_d010_v3_1776076197178.png',
    'D011': 'rose_falooda_d011_v3_retry1_1776076226928.png',
    'D012': 'shikanji_d012_v3_retry1_1776076242857.png',
    'D013': 'thandai_d013_v3_retry1_1776076259643.png',
    'DE011': 'rasmalai_de011_v3_retry1_1776076279938.png',
    'DE012': 'malpua_rabri_de012_v3_retry1_1776076296652.png',
    'DE013': 'moong_dal_halwa_de013_v3_retry1_1776076312110.png',
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
    print("Starting deployment of Batch 5 images (8 successful ones)...")
    deploy_images(mapping)
    print("Deployment completed.")
