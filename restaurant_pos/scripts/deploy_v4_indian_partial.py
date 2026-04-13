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

# Mapping of SKU to filename (Successful ones from this batch)
mapping = {
    'S010': 'soya_chaap_tikka_s010_1775992705398.png',
    'S011': 'hara_bhara_kebab_s011_1775992721776.png',
    'S012': 'fish_amritsari_s012_1775992737474.png',
    'S013': 'murg_malai_kebab_s013_1775992757153.png',
    'IV010': 'paneer_lababdar_iv010_1775992771801.png',
    'IV011': 'methi_matar_malai_iv011_1775992844058.png',
    'IV012': 'dal_tadka_iv012_1775992859187.png',
}

def deploy_batch(batch_mapping):
    for sku, filename in batch_mapping.items():
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
    print("Starting partial deployment of Indian Style expansion (First 7 images)...")
    deploy_batch(mapping)
    print("Partial deployment completed.")
