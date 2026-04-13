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
    'CP001': 'penne_arrabbiata_cp001_final_1775893842286.png',
    'CP002': 'mushroom_alfredo_cp002_final_1775893857764.png',
    'CP003': 'bbq_wings_cp003_final_1775893874621.png',
    'CP004': 'loaded_nachos_cp004_final_1775893890865.png',
    'HS001': 'greek_salad_hs001_final_1775893904463.png',
    'HS002': 'quinoa_bowl_hs002_final_1775893925166.png',
    'IS001': 'chole_bhature_is001_final_1775893941242.png',
    'IS002': 'tandoori_platter_is002_final_1775893957267.png',
    'PB001': 'butter_pav_bhaji_pb001_final_1775893972324.png',
    'PB002': 'cheese_pav_bhaji_pb002_final_1775893984842.png',
    'PB003': 'paneer_pav_bhaji_pb003_final_1775893998667.png',
    'PB004': 'kada_pav_bhaji_pb004_final_1775894013214.png',
    'PB005': 'jain_pav_bhaji_pb005_final_1775894026510.png',
    'DE010': 'death_by_chocolate_de010_final_1775894041103.png',
    'D020': 'mango_mastani_d020_final_1775894056857.png',
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
    print("Starting deployment of expansion batch images...")
    deploy_batch(mapping)
    print("Deployment completed.")
