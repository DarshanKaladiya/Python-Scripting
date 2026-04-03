from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Order
from orders.services import create_order

from .models import DiningSection, RestaurantTable


class FloorManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="captain", password="pass123", role="captain")
        self.section_main = DiningSection.objects.create(name="Main Hall", color_code="#f97316")
        self.section_patio = DiningSection.objects.create(name="Patio", color_code="#16a34a")
        self.table_one = RestaurantTable.objects.create(section=self.section_main, name="T1", seats=4, status=RestaurantTable.Status.AVAILABLE)
        self.table_two = RestaurantTable.objects.create(section=self.section_main, name="T2", seats=4, status=RestaurantTable.Status.AVAILABLE)
        self.table_three = RestaurantTable.objects.create(section=self.section_patio, name="P1", seats=2, status=RestaurantTable.Status.RESERVED)

    def test_floor_management_screen_renders_sections_and_tables(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("floor:management"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Floor Control")
        self.assertContains(response, self.section_main.name)
        self.assertContains(response, self.table_one.name)

    def test_open_table_order_creates_order_and_redirects_to_pos(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("floor:open-table-order", kwargs={"table_id": self.table_one.id}))
        order = Order.objects.get(table=self.table_one)
        self.table_one.refresh_from_db()

        self.assertRedirects(response, f"{reverse('orders:pos')}?order_id={order.id}", fetch_redirect_response=False)
        self.assertEqual(order.order_type, Order.OrderType.DINE_IN)
        self.assertEqual(self.table_one.status, RestaurantTable.Status.OCCUPIED)

    def test_transfer_table_order_moves_active_order_to_new_table(self):
        order = create_order(order_type=Order.OrderType.DINE_IN, created_by=self.user, table=self.table_one, waiter=self.user)
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("floor:transfer-order", kwargs={"order_id": order.id}),
            data={"target_table_id": self.table_three.id},
        )
        order.refresh_from_db()
        self.table_one.refresh_from_db()
        self.table_three.refresh_from_db()

        self.assertRedirects(response, reverse("floor:management"), fetch_redirect_response=False)
        self.assertEqual(order.table, self.table_three)
        self.assertEqual(self.table_one.status, RestaurantTable.Status.AVAILABLE)
        self.assertEqual(self.table_three.status, RestaurantTable.Status.OCCUPIED)
