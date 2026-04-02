from django.db import models


class ExternalOrder(models.Model):
    class Source(models.TextChoices):
        SWIGGY = "swiggy", "Swiggy"
        ZOMATO = "zomato", "Zomato"
        ONDC = "ondc", "ONDC"
        MANUAL = "manual", "Manual"

    class SyncStatus(models.TextChoices):
        RECEIVED = "received", "Received"
        MAPPED = "mapped", "Mapped"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    source = models.CharField(max_length=20, choices=Source.choices)
    external_order_id = models.CharField(max_length=80)
    idempotency_key = models.CharField(max_length=120, unique=True)
    payload_snapshot = models.JSONField(default=dict)
    mapped_items = models.JSONField(default=list, blank=True)
    sync_status = models.CharField(max_length=20, choices=SyncStatus.choices, default=SyncStatus.RECEIVED)
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.SET_NULL)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("source", "external_order_id")

    def __str__(self):
        return f"{self.source} {self.external_order_id}"

# Create your models here.
