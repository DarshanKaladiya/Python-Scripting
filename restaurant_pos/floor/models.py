from django.conf import settings
from django.db import models


class DiningSection(models.Model):
    name = models.CharField(max_length=80)
    color_code = models.CharField(max_length=20, default="#198754")

    def __str__(self):
        return self.name


class RestaurantTable(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        OCCUPIED = "occupied", "Occupied"
        RESERVED = "reserved", "Reserved"
        DIRTY = "dirty", "Dirty"

    section = models.ForeignKey(DiningSection, related_name="tables", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    seats = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("section", "name")
        ordering = ["section__name", "name"]

    def __str__(self):
        return self.name


class WaiterAssignment(models.Model):
    table = models.ForeignKey(RestaurantTable, related_name="assignments", on_delete=models.CASCADE)
    waiter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="table_assignments", on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.waiter} -> {self.table}"

# Create your models here.
