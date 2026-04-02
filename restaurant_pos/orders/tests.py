from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import PaymentMethod, TaxRate
from customers.models import Customer, LoyaltyRule
from floor.models import DiningSection, RestaurantTable
from inventory.models import Ingredient, StockLedger, Unit
from menu.models import MenuCategory, MenuItem
from recipes.models import Recipe, RecipeLine

from .models import Order
from .services import add_item_to_order, create_order, send_kot, settle_order


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

# Create your tests here.
