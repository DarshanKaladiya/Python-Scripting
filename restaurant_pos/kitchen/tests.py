import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import PaymentMethod, TaxRate
from menu.models import MenuCategory, MenuItem
from orders.services import add_item_to_order, create_order, send_kot


class KitchenStatusTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="chef", password="pass123", role="kitchen")
        PaymentMethod.objects.create(code="cash", name="Cash", is_cash=True)
        tax = TaxRate.objects.create(name="GST 5", rate_percent=Decimal("5.00"))
        category = MenuCategory.objects.create(name="Starters")
        item = MenuItem.objects.create(category=category, tax_rate=tax, name="Paneer Tikka", sku="PT-1", base_price=Decimal("250.00"))
        order = create_order(order_type="dine_in", created_by=self.user)
        add_item_to_order(order=order, menu_item=item, quantity=1)
        self.kot = send_kot(order=order, user=self.user)
        self.kot_item = self.kot.items.first()

    def test_kds_status_updates_order_item(self):
        self.client.force_login(self.user)
        url = reverse("kitchen:update-item-status", kwargs={"kot_item_id": self.kot_item.id})
        response = self.client.post(url, data=json.dumps({"status": "ready"}), content_type="application/json")
        self.kot_item.order_item.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.kot_item.order_item.status, "ready")

# Create your tests here.
