import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_pos.settings')
django.setup()

from tables.models import FloorSection, Table

def seed_floor():
    # 1. Clear existing
    FloorSection.objects.all().delete()
    
    # 2. Main Hall
    main_hall = FloorSection.objects.create(name='Main Hall')
    
    tables = [
        {'name': 'T1', 'x_pos': 10, 'y_pos': 15, 'width': 80, 'height': 80, 'shape': 'circle', 'capacity': 2},
        {'name': 'T2', 'x_pos': 30, 'y_pos': 15, 'width': 80, 'height': 80, 'shape': 'circle', 'capacity': 2},
        {'name': 'T3', 'x_pos': 50, 'y_pos': 15, 'width': 100, 'height': 100, 'shape': 'square', 'capacity': 4},
        {'name': 'T4', 'x_pos': 10, 'y_pos': 45, 'width': 150, 'height': 100, 'shape': 'rectangle', 'capacity': 6},
        {'name': 'T5', 'x_pos': 40, 'y_pos': 45, 'width': 150, 'height': 100, 'shape': 'rectangle', 'capacity': 6},
        {'name': 'T6', 'x_pos': 70, 'y_pos': 45, 'width': 100, 'height': 100, 'shape': 'square', 'capacity': 4},
    ]
    
    for t_data in tables:
        Table.objects.create(section=main_hall, **t_data)
        
    # 3. Rooftop
    rooftop = FloorSection.objects.create(name='Rooftop Garden')
    Table.objects.create(section=rooftop, name='R1', x_pos=20, y_pos=20, width=120, height=120, shape='circle', capacity=4)
    Table.objects.create(section=rooftop, name='R2', x_pos=50, y_pos=20, width=120, height=120, shape='circle', capacity=4)

    print("Visual Floor Layout Seeded Successfully!")

if __name__ == '__main__':
    seed_floor()
