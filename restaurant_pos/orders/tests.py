from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import PaymentMethod, TaxRate
from customers.models import Customer, LoyaltyRule
from floor.models import DiningSection, RestaurantTable
from inventory.models import Ingredient, StockLedger, Unit
from menu.models import MenuCategory, MenuItem, ModifierGroup, ModifierOption
from recipes.models import Recipe, RecipeLine

from .models import Order
from .services import add_item_to_order, create_order, resolve_modifier_selection, send_kot, settle_order


class OrderFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cashier", password="pass123", role="cashier")
        self.tax = TaxRate.objects.create(name="GST 5", rate_percent=Decimal("5.00"))
        self.cash = PaymentMethod.objects.create(code="cash", name="Cash", is_cash=True)
        self.category = MenuCategory.objects.create(name="Starters")
        self.item = MenuItem.objects.create(category=self.category, tax_rate=self.tax, name="Paneer Tikka", sku="PT-1", base_price=Decimal("250.00"))
        self.unit = Unit.objects.create(name="Gram", short_code="g")
        self.ingredient = Ingredient.objects.create(name="Paneer", sku="ING-1", unit=self.unit, current_stock=Decimal("1000"), reorder_level=Decimal("100"))
        recipe = Recipe.objects.create(menu_item=self.item)
        RecipeLine.objects.create(recipe=recipe, ingredient=self.ingredient, quantity=Decimal("200"), wastage_percent=Decimal("0"))
        self.customer = Customer.objects.create(name="Demo Customer", phone_number="9998887776")
        LoyaltyRule.objects.create(points_per_rupee=Decimal("0.10"), redeem_value_per_point=Decimal("1.00"), minimum_points_to_redeem=Decimal("10"))
        section = DiningSection.objects.create(name="Main Hall")
        self.table = RestaurantTable.objects.create(section=section, name="T1")

    def test_settle_order_deducts_stock_and_awards_loyalty(self):
        order = create_order(order_type=Order.OrderType.DINE_IN, created_by=self.user, table=self.table, customer=self.customer)
        add_item_to_order(order=order, menu_item=self.item, quantity=Decimal("2"))
        send_kot(order=order, user=self.user)
        settle_order(order=order, user=self.user, payments=[{"method": self.cash, "amount": Decimal("525.00")}])
        order.refresh_from_db()
        self.ingredient.refresh_from_db()
        self.customer.refresh_from_db()

        self.assertEqual(order.status, Order.Status.COMPLETED)
        self.assertEqual(self.ingredient.current_stock, Decimal("600"))
        self.assertTrue(StockLedger.objects.filter(reference_type="order", reference_id=order.id).exists())
        self.assertGreater(self.customer.loyalty_points, 0)

    def test_add_item_api_rejects_missing_required_modifier(self):
        group = ModifierGroup.objects.create(name="Spice Level", selection_type=ModifierGroup.SelectionType.SINGLE, is_required=True)
        option = ModifierOption.objects.create(group=group, name="Medium", price_delta=Decimal("0.00"))
        self.item.modifier_groups.add(group)
        order = create_order(order_type=Order.OrderType.DINE_IN, created_by=self.user, table=self.table)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("orders:add-item", kwargs={"order_id": order.id}),
            data='{"menu_item_id": %s, "quantity": 1, "modifiers": []}' % self.item.id,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Spice Level", response.json()["error"])
        self.assertEqual(option.price_delta, Decimal("0.00"))

    def test_add_item_api_saves_modifier_snapshot_note_and_price_delta(self):
        group = ModifierGroup.objects.create(name="Add-ons", selection_type=ModifierGroup.SelectionType.MULTIPLE, is_required=False)
        option = ModifierOption.objects.create(group=group, name="Extra Cheese", price_delta=Decimal("40.00"))
        self.item.modifier_groups.add(group)
        order = create_order(order_type=Order.OrderType.DINE_IN, created_by=self.user, table=self.table)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("orders:add-item", kwargs={"order_id": order.id}),
            data='{"menu_item_id": %s, "quantity": 1, "modifiers": [%s], "notes": "Less spicy"}' % (self.item.id, option.id),
            content_type="application/json",
        )
        order.refresh_from_db()
        order_item = order.items.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(order_item.unit_price, Decimal("290.00"))
        self.assertEqual(order_item.notes, "Less spicy")
        self.assertEqual(
            order_item.modifiers_snapshot,
            [{"group_name": "Add-ons", "option_name": "Extra Cheese", "price_delta": "40.00"}],
        )
        payload = response.json()["order"]["items"][0]
        self.assertEqual(payload["notes"], "Less spicy")
        self.assertEqual(payload["modifiers"][0]["option_name"], "Extra Cheese")

    def test_resolve_modifier_selection_rejects_invalid_option_for_item(self):
        group = ModifierGroup.objects.create(name="Size")
        option = ModifierOption.objects.create(group=group, name="Large", price_delta=Decimal("20.00"))

        with self.assertRaisesMessage(ValueError, "not valid for this item"):
            resolve_modifier_selection(menu_item=self.item, selected_option_ids=[option.id])

# Create your tests here.
