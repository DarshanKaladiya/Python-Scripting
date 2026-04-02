from django.db import models


class MenuCategory(models.Model):
    name = models.CharField(max_length=80)
    color_code = models.CharField(max_length=20, default="#0d6efd")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class ModifierGroup(models.Model):
    class SelectionType(models.TextChoices):
        SINGLE = "single", "Single"
        MULTIPLE = "multiple", "Multiple"

    name = models.CharField(max_length=80)
    selection_type = models.CharField(max_length=20, choices=SelectionType.choices, default=SelectionType.SINGLE)
    is_required = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ModifierOption(models.Model):
    group = models.ForeignKey(ModifierGroup, related_name="options", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    price_delta = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    class ItemType(models.TextChoices):
        VEG = "veg", "Veg"
        NON_VEG = "non_veg", "Non-Veg"
        BEVERAGE = "beverage", "Beverage"
        OTHER = "other", "Other"

    category = models.ForeignKey(MenuCategory, related_name="items", on_delete=models.PROTECT)
    tax_rate = models.ForeignKey("core.TaxRate", on_delete=models.SET_NULL, null=True, blank=True)
    modifier_groups = models.ManyToManyField(ModifierGroup, blank=True, related_name="menu_items")
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=40, unique=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    item_type = models.CharField(max_length=20, choices=ItemType.choices, default=ItemType.VEG)
    short_name = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    track_inventory = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__sort_order", "name"]

    def __str__(self):
        return self.name

# Create your models here.
