from django.db import models

class AggregatorWebhookLog(models.Model):
    source = models.CharField(max_length=50) # zomato, swiggy
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} - {self.received_at}"
