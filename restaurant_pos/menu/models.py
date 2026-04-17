from django.db import models
from inventory.models import RawMaterial

class Category(models.Model):
    STATION_CHOICES = (
        ('kitchen', 'Main Kitchen'),
        ('bar', 'Bar / Drinks'),
        ('pantry', 'Pantry / Desserts'),
        ('tandoor', 'Tandoor / Oven'),
    )
    name = models.CharField(max_length=100)
    kitchen_station = models.CharField(max_length=20, choices=STATION_CHOICES, default='kitchen')
    color_code = models.CharField(max_length=20, default="#f97316")
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    ITEM_TYPE_CHOICES = (
        ('veg', 'Vegetarian'),
        ('non_veg', 'Non-Vegetarian'),
        ('egg', 'Contains Egg'),
    )
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='veg')
    image = models.ImageField(upload_to='menu_items/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class RecipeIngredient(models.Model):
    menu_item = models.ForeignKey(MenuItem, related_name='recipe_ingredients', on_delete=models.CASCADE)
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=3, help_text="Amount of raw material to deduct per order")

    def __str__(self):
        return f"{self.menu_item.name} needs {self.quantity_required} {self.raw_material.unit.short_code} of {self.raw_material.name}"
