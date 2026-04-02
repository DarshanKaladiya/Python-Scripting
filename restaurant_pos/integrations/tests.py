import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import TaxRate
from menu.models import MenuCategory, MenuItem
from orders.models import Order

from .models import ExternalOrder


class IntegrationWebhookTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user(username="cashier", password="pass123", role="cashier")
        tax = TaxRate.objects.create(name="GST 5", rate_percent=Decimal("5.00"))
        category = MenuCategory.objects.create(name="Starters")
        MenuItem.objects.create(category=category, tax_rate=tax, name="Paneer Tikka", sku="PT-1", base_price=Decimal("250.00"))

    def test_webhook_is_idempotent(self):
        url = reverse("integrations:provider-order-webhook", kwargs={"provider": "swiggy"})
        payload = {"order_id": "SW-1001", "items": [{"name": "Paneer Tikka", "quantity": 1}]}

        first = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        second = self.client.post(url, data=json.dumps(payload), content_type="application/json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(ExternalOrder.objects.count(), 1)
        self.assertEqual(Order.objects.count(), 1)
        self.assertTrue(second.json()["duplicate"])
