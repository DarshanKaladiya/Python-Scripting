from decimal import Decimal

from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    loyalty_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    last_visit = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name", "phone_number"]

    def __str__(self):
        return self.name or self.phone_number

    def add_points(self, points):
        self.loyalty_points += Decimal(points)
        self.save(update_fields=["loyalty_points"])


class LoyaltyRule(models.Model):
    points_per_rupee = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    redeem_value_per_point = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    minimum_points_to_redeem = models.DecimalField(max_digits=8, decimal_places=2, default=100)
    manager_approval_required = models.BooleanField(default=True)

    def __str__(self):
        return "Default Loyalty Rule"

# Create your models here.
