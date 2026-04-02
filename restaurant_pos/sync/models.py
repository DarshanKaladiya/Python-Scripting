from django.db import models


class Terminal(models.Model):
    name = models.CharField(max_length=80)
    code = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class OfflineAction(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    terminal = models.ForeignKey(Terminal, related_name="offline_actions", on_delete=models.CASCADE)
    idempotency_key = models.CharField(max_length=120, unique=True)
    action_type = models.CharField(max_length=80)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=255, blank=True)
    linked_order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.idempotency_key

# Create your models here.
