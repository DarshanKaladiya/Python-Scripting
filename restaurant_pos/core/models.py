from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OutletProfile(TimeStampedModel):
    name = models.CharField(max_length=150)
    legal_name = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    currency_code = models.CharField(max_length=10, default="INR")
    invoice_prefix = models.CharField(max_length=10, default="INV")
    kot_prefix = models.CharField(max_length=10, default="KOT")

    def __str__(self):
        return self.name


class TaxRate(TimeStampedModel):
    name = models.CharField(max_length=50)
    rate_percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.rate_percent}%)"


class PaymentMethod(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    is_cash = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Printer(TimeStampedModel):
    name = models.CharField(max_length=80)
    printer_type = models.CharField(max_length=30, default="browser")
    location = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class AppSetting(TimeStampedModel):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.key


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.PositiveBigIntegerField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.entity_type}"

# Create your models here.
