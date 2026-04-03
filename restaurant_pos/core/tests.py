from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from floor.models import DiningSection, RestaurantTable
from inventory.models import Ingredient, Unit
from orders.models import Order


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="manager", password="pass123", role="manager")
        section = DiningSection.objects.create(name="Main Hall")
        table = RestaurantTable.objects.create(
            section=section,
            name="T1",
            status=RestaurantTable.Status.OCCUPIED,
        )
        unit = Unit.objects.create(name="Kilogram", short_code="kg")
        self.ingredient = Ingredient.objects.create(
            name="Paneer",
            sku="ING-001",
            unit=unit,
            current_stock=Decimal("2.000"),
            reorder_level=Decimal("5.000"),
        )
        self.order = Order.objects.create(
            order_number="ORD00001",
            order_type=Order.OrderType.DINE_IN,
            status=Order.Status.COMPLETED,
            subtotal=Decimal("552.38"),
            tax_amount=Decimal("27.62"),
            total_amount=Decimal("580.00"),
            table=table,
            created_by=self.user,
            updated_by=self.user,
        )

    def test_dashboard_renders_pos_style_operations_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Operations Command")
        self.assertContains(response, self.order.order_number)
        self.assertContains(response, self.ingredient.name)

    def test_dashboard_summary_api_returns_live_metrics(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["today_sales"], "580")
        self.assertEqual(payload["orders_today"], 1)
        self.assertEqual(payload["open_tables"], 1)
        self.assertEqual(payload["low_stock_count"], 1)
        self.assertEqual(len(payload["recent_orders"]), 1)
        self.assertEqual(payload["recent_orders"][0]["order_number"], self.order.order_number)
        self.assertEqual(payload["recent_orders"][0]["table_name"], "T1")
        self.assertEqual(len(payload["low_stock_items"]), 1)
        self.assertEqual(payload["low_stock_items"][0]["name"], self.ingredient.name)
        self.assertEqual(payload["table_status"][0]["status"], RestaurantTable.Status.OCCUPIED)
