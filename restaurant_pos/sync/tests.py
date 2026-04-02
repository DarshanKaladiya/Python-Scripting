import json

from django.test import TestCase
from django.urls import reverse

from .models import OfflineAction


class SyncEndpointTests(TestCase):
    def test_offline_action_is_idempotent(self):
        url = reverse("sync:offline-actions")
        payload = {
            "terminal_code": "cashier-1",
            "terminal_name": "Cashier 1",
            "idempotency_key": "demo-action-1",
            "action_type": "settle_order",
            "payload": {"order_id": 10},
        }
        first = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        second = self.client.post(url, data=json.dumps(payload), content_type="application/json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(OfflineAction.objects.count(), 1)

# Create your tests here.
