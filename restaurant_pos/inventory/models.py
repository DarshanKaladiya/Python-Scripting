from decimal import Decimal

from django.conf import settings
from django.db import models


class Unit(models.Model):
    name = models.CharField(max_length=50)
    short_code = models.CharField(max_length=10, unique=True)
    allow_decimal = models.BooleanField(default=True)

    def __str__(self):
        return self.short_code


class Vendor(models.Model):
    name = models.CharField(max_length=120)
    contact_person = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=40, unique=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    current_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.current_stock <= self.reorder_level


class PurchaseEntry(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number


class PurchaseItem(models.Model):
    entry = models.ForeignKey(PurchaseEntry, related_name="items", on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_applied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.ingredient} x {self.quantity}"


class StockLedger(models.Model):
    class TxnType(models.TextChoices):
        PURCHASE = "purchase", "Purchase"
        SALE_DEDUCTION = "sale_deduction", "Sale Deduction"
        REVERSAL = "reversal", "Reversal"
        ADJUSTMENT = "adjustment", "Adjustment"
        WASTAGE = "wastage", "Wastage"

    ingredient = models.ForeignKey(Ingredient, related_name="ledger_entries", on_delete=models.PROTECT)
    txn_type = models.CharField(max_length=30, choices=TxnType.choices)
    quantity_change = models.DecimalField(max_digits=12, decimal_places=3)
    balance_after = models.DecimalField(max_digits=12, decimal_places=3)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.PositiveBigIntegerField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    reversal_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.ingredient} {self.txn_type} {self.quantity_change}"


class WastageEntry(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.CharField(max_length=120)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ingredient} wastage"


class StockAdjustment(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    quantity_change = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    reason = models.CharField(max_length=120)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ingredient} adjustment"

# Create your models here.
