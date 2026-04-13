import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from accounts.models import User

def seed_users():
    users = [
        ('admin_user', 'admin123', 'admin'),
        ('chef_user', 'chef123', 'chef'),
        ('customer_user', 'customer123', 'customer'),
        ('cashier_user', 'cashier123', 'cashier'),
    ]
    
    for username, password, role in users:
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, password=password, role=role)
            print(f"Created {role} user: {username}")
        else:
            print(f"User {username} already exists.")

if __name__ == '__main__':
    seed_users()
