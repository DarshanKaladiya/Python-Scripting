from django.db import models

class Unit(models.Model):
    name = models.CharField(max_length=50)
    short_code = models.CharField(max_length=10)

    def __str__(self):
        return self.short_code

class Supplier(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class RawMaterial(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    current_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit.short_code})"
