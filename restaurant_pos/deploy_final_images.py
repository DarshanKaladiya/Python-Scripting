import os
import shutil
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from menu.models import MenuItem

# Source directory (Brain directory for this session)
# Update this path if the session changes
src_dir = r"C:\Users\DARSHAN\.gemini\antigravity\brain\a7a4facc-56bd-4ab0-a389-c71908269b44"
# Destination directory (Media)
dest_dir = r"d:\Intership\Python Automation\restaurant_pos\media\menu_items"

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Mapping of SKU to filename (Update this as images are generated)
mapping = {
    'M004': 'chicken_biryani_m004_1775813700649.png',
}

def deploy_images(batch_mapping):
    for sku, filename in batch_mapping.items():
        src_path = os.path.join(src_dir, filename)
        if os.path.exists(src_path):
            # Target clean filename
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
    print("Starting final image deployment...")
    deploy_images(mapping)
    print("Deployment cycle completed.")
