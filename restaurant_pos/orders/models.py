from decimal import Decimal

from django.conf import settings
from django.db import models


class Order(models.Model):
    class OrderType(models.TextChoices):
        DINE_IN = "dine_in", "Dine In"
        TAKEAWAY = "takeaway", "Takeaway"
        DELIVERY = "delivery", "Delivery"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        KOT_SENT = "kot_sent", "KOT Sent"
        IN_PROGRESS = "in_progress", "In Progress"
        READY = "ready", "Ready"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PARTIAL = "partial", "Partial"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        SWIGGY = "swiggy", "Swiggy"
        ZOMATO = "zomato", "Zomato"
        ONDC = "ondc", "ONDC"

    order_number = models.CharField(max_length=30, unique=True)
    invoice_number = models.CharField(max_length=30, blank=True)
    order_type = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.DINE_IN)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    table = models.ForeignKey("floor.RestaurantTable", null=True, blank=True, on_delete=models.SET_NULL)
    customer = models.ForeignKey("customers.Customer", null=True, blank=True, on_delete=models.SET_NULL)
    waiter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="served_orders", on_delete=models.SET_NULL)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    is_held = models.BooleanField(default=False)
    stock_posted = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_orders", null=True, blank=True, on_delete=models.SET_NULL)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="updated_orders", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number

    def recalculate_totals(self):
        active_items = self.items.exclude(status=OrderItem.Status.CANCELLED)
        subtotal = sum((item.unit_price * item.quantity for item in active_items), Decimal("0"))
        line_discounts = sum((item.line_discount for item in active_items), Decimal("0"))
        taxable = subtotal - line_discounts - self.discount_amount
        tax = sum((item.tax_amount for item in active_items), Decimal("0"))
        self.subtotal = subtotal
        self.tax_amount = tax
        self.total_amount = max(taxable + tax, Decimal("0"))
        return self.total_amount


class OrderItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        SERVED = "served", "Served"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey("menu.MenuItem", on_delete=models.PROTECT)
    item_name_snapshot = models.CharField(max_length=120)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate_snapshot = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)
    modifiers_snapshot = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    sent_to_kitchen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_name_snapshot

    @property
    def tax_amount(self):
        taxable = (self.unit_price * self.quantity) - self.line_discount
        return taxable * (self.tax_rate_snapshot / Decimal("100"))

    @property
    def total_price(self):
        taxable = (self.unit_price * self.quantity) - self.line_discount
        return taxable + self.tax_amount


class KitchenOrderTicket(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        SERVED = "served", "Served"

    order = models.ForeignKey(Order, related_name="kots", on_delete=models.CASCADE)
    kot_number = models.CharField(max_length=30, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    source = models.CharField(max_length=20, default=Order.Source.MANUAL)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.kot_number


class KOTItem(models.Model):
    kot = models.ForeignKey(KitchenOrderTicket, related_name="items", on_delete=models.CASCADE)
    order_item = models.ForeignKey(OrderItem, related_name="kot_items", on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=KitchenOrderTicket.Status.choices, default=KitchenOrderTicket.Status.NEW)

    def __str__(self):
        return f"{self.kot} - {self.order_item}"


class Payment(models.Model):
    order = models.ForeignKey(Order, related_name="payments", on_delete=models.CASCADE)
    method = models.ForeignKey("core.PaymentMethod", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=60, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order} - {self.amount}"

# Create your models here.
