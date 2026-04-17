from django.db import models
from decimal import Decimal
from accounts.models import User
from menu.models import MenuItem
from tables.models import Table
import uuid

class Order(models.Model):
    ORDER_TYPE_CHOICES = (
        ('dine_in', 'Dine In'),
        ('takeaway', 'Takeaway'),
        ('delivery', 'Delivery'),
        ('aggregator', 'Aggregator (Zomato/Swiggy)'),
    )
    STATUS_CHOICES = (
        ('draft', 'Draft / Ordering'),
        ('awaiting_confirmation', 'Awaiting Confirmation'),
        ('kot_sent', 'KOT Sent'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed/Billed'),
        ('cancelled', 'Cancelled'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    )
    
    order_number = models.CharField(max_length=20, unique=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='dine_in')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    guest_count = models.IntegerField(default=1)
    
    # Customer Details
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    customer_phone = models.CharField(max_length=15, null=True, blank=True)
    
    table = models.ForeignKey(Table, null=True, blank=True, on_delete=models.SET_NULL)
    additional_tables = models.ManyToManyField(Table, related_name='joined_orders', blank=True)
    waiter = models.ForeignKey(User, null=True, blank=True, related_name='taken_orders', on_delete=models.SET_NULL)
    customer_user = models.ForeignKey(User, null=True, blank=True, related_name='customer_orders', on_delete=models.SET_NULL)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total tax (cgst + sgst)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tracking fields
    offline_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tracking_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.order_number

    def calculate_totals(self, force_subtotal=None):
        """Calculates subtotal, taxes, and final total based on order items."""
        from .models import OrderItem
        
        if force_subtotal is not None:
            self.subtotal = Decimal(str(force_subtotal))
        else:
            items = OrderItem.objects.filter(order=self)
            subtotal = sum(item.price * item.quantity for item in items)
            self.subtotal = Decimal(str(subtotal))
        
        # Standard 5% GST (2.5% CGST + 2.5% SGST)
        self.cgst = self.subtotal * Decimal('0.025')
        self.sgst = self.subtotal * Decimal('0.025')
        self.tax = self.cgst + self.sgst
        
        # Grand Total
        self.total_amount = self.subtotal + self.tax + self.service_charge
        self.save()


class OrderItem(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
    )
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # If item status changed to 'ready', check if all items in order are ready
        if not is_new and self.status == 'ready':
            order = self.order
            if not order.items.filter(status__in=['pending', 'preparing']).exists():
                if order.status != 'ready':
                    order.status = 'ready'
                    order.save()
        elif not is_new and self.status == 'preparing':
            order = self.order
            if order.status == 'kot_sent':
                order.status = 'preparing'
                order.save()

class KitchenOrderTicket(models.Model):
    order = models.ForeignKey(Order, related_name='kots', on_delete=models.CASCADE)
    kot_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_printed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"KOT #{self.kot_number} for {self.order.order_number}"
