import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import PaymentMethod, TaxRate
from floor.models import DiningSection, RestaurantTable
from menu.models import MenuCategory, MenuItem, ModifierGroup, ModifierOption
from orders.models import KitchenOrderTicket, OrderItem
from orders.services import add_item_to_order, create_order, resolve_modifier_selection, send_kot


class KitchenStatusTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="chef", password="pass123", role="kitchen")
        PaymentMethod.objects.create(code="cash", name="Cash", is_cash=True)
        tax = TaxRate.objects.create(name="GST 5", rate_percent=Decimal("5.00"))
        category = MenuCategory.objects.create(name="Starters")
        self.item = MenuItem.objects.create(category=category, tax_rate=tax, name="Paneer Tikka", sku="PT-1", base_price=Decimal("250.00"))
        spice_group = ModifierGroup.objects.create(name="Spice Level", selection_type=ModifierGroup.SelectionType.SINGLE, is_required=True)
        spicy_option = ModifierOption.objects.create(group=spice_group, name="Spicy", price_delta=Decimal("0.00"))
        self.item.modifier_groups.add(spice_group)
        modifier_snapshot, modifier_price_delta = resolve_modifier_selection(menu_item=self.item, selected_option_ids=[spicy_option.id])
        order = create_order(order_type="dine_in", created_by=self.user)
        add_item_to_order(
            order=order,
            menu_item=self.item,
            quantity=1,
            notes="No onion",
            modifiers=modifier_snapshot,
            modifier_price_delta=modifier_price_delta,
        )
        self.kot = send_kot(order=order, user=self.user)
        self.kot_item = self.kot.items.first()
        section = DiningSection.objects.create(name="Pass")
        table = RestaurantTable.objects.create(section=section, name="T2")

        ready_order = create_order(order_type="dine_in", created_by=self.user, table=table)
        add_item_to_order(order=ready_order, menu_item=self.item, quantity=2, notes="Extra spicy")
        self.ready_kot = send_kot(order=ready_order, user=self.user)
        self.ready_item = self.ready_kot.items.first()
        self.ready_item.status = KitchenOrderTicket.Status.READY
        self.ready_item.save(update_fields=["status"])
        self.ready_item.order_item.status = OrderItem.Status.READY
        self.ready_item.order_item.save(update_fields=["status"])

        served_order = create_order(order_type="takeaway", created_by=self.user)
        add_item_to_order(order=served_order, menu_item=self.item, quantity=1)
        self.served_kot = send_kot(order=served_order, user=self.user)
        self.served_item = self.served_kot.items.first()
        self.served_item.status = KitchenOrderTicket.Status.SERVED
        self.served_item.save(update_fields=["status"])
        self.served_item.order_item.status = OrderItem.Status.SERVED
        self.served_item.order_item.save(update_fields=["status"])

    def test_kds_screen_groups_active_items_by_lane(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("kitchen:screen"))
        lanes = {lane["key"]: [item.id for item in lane["items"]] for lane in response.context["lanes"]}

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New Lane")
        self.assertContains(response, "Ready Lane")
        self.assertIn(self.kot_item.id, lanes[KitchenOrderTicket.Status.NEW])
        self.assertIn(self.ready_item.id, lanes[KitchenOrderTicket.Status.READY])
        self.assertNotIn(self.served_item.id, sum(lanes.values(), []))
        self.assertNotContains(response, self.served_kot.kot_number)
        self.assertContains(response, "Spice Level: Spicy")
        self.assertContains(response, "No onion")

    def test_kds_status_updates_order_item(self):
        self.client.force_login(self.user)
        url = reverse("kitchen:update-item-status", kwargs={"kot_item_id": self.kot_item.id})
        response = self.client.post(url, data=json.dumps({"status": "ready"}), content_type="application/json")
        self.kot_item.order_item.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.kot_item.order_item.status, "ready")

# Create your tests here.
