from django.db import models

import uuid

class FloorSection(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Table(models.Model):
    section = models.ForeignKey(FloorSection, related_name='tables', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    capacity = models.IntegerField(default=4)
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    qr_code_uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Layout fields
    x_pos = models.IntegerField(default=0, help_text="X position in percentage (0-100)")
    y_pos = models.IntegerField(default=0, help_text="Y position in percentage (0-100)")
    width = models.IntegerField(default=100, help_text="Width in pixels")
    height = models.IntegerField(default=100, help_text="Height in pixels")
    SHAPE_CHOICES = (
        ('square', 'Square'),
        ('rectangle', 'Rectangle'),
        ('circle', 'Circle'),
    )
    shape = models.CharField(max_length=20, choices=SHAPE_CHOICES, default='square')
    attached_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='attachments')

    def __str__(self):
        return f"{self.section.name} - {self.name}"

class FloorDecor(models.Model):
    DECOR_TYPE_CHOICES = (
        ('plant', 'Plant / Greenery'),
        ('wall', 'Wall / Partition'),
        ('counter', 'Counter / Bar'),
        ('pillar', 'Pillar'),
    )
    SHAPE_CHOICES = (
        ('square', 'Square'),
        ('rectangle', 'Rectangle'),
        ('circle', 'Circle'),
    )
    section = models.ForeignKey(FloorSection, related_name='decor_items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    decor_type = models.CharField(max_length=20, choices=DECOR_TYPE_CHOICES, default='plant')
    shape = models.CharField(max_length=20, choices=SHAPE_CHOICES, default='square')
    
    # Layout fields
    x_pos = models.IntegerField(default=0)
    y_pos = models.IntegerField(default=0)
    width = models.IntegerField(default=50)
    height = models.IntegerField(default=50)

    def __str__(self):
        return f"{self.get_decor_type_display()} in {self.section.name}"
