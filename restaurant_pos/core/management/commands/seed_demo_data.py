from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import OutletProfile, PaymentMethod, TaxRate
from customers.models import Customer, LoyaltyRule
from floor.models import DiningSection, RestaurantTable
from inventory.models import Ingredient, Unit
from menu.models import MenuCategory, MenuItem
from recipes.models import Recipe, RecipeLine


class Command(BaseCommand):
    help = "Seed demo data for the restaurant POS MVP"

    def handle(self, *args, **options):
        User = get_user_model()

        OutletProfile.objects.get_or_create(
            name="Demo Restaurant",
            defaults={
                "legal_name": "Demo Restaurant Private Limited",
                "address": "Main Market Road, Ahmedabad",
                "phone": "9999999999",
                "gstin": "24ABCDE1234F1Z5",
            },
        )
        gst5, _ = TaxRate.objects.get_or_create(name="GST 5%", defaults={"rate_percent": Decimal("5.00")})
        PaymentMethod.objects.get_or_create(code="cash", defaults={"name": "Cash", "is_cash": True})
        PaymentMethod.objects.get_or_create(code="upi", defaults={"name": "UPI", "is_cash": False})
        PaymentMethod.objects.get_or_create(code="card", defaults={"name": "Card", "is_cash": False})
        LoyaltyRule.objects.get_or_create(
            id=1,
            defaults={
                "points_per_rupee": Decimal("0.10"),
                "redeem_value_per_point": Decimal("1.00"),
                "minimum_points_to_redeem": Decimal("100"),
                "manager_approval_required": True,
            },
        )

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "POS",
                "last_name": "Admin",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()

        cashier, created = User.objects.get_or_create(
            username="cashier",
            defaults={"first_name": "Demo", "last_name": "Cashier", "role": User.Role.CASHIER},
        )
        if created:
            cashier.set_password("cash123")
            cashier.save()

        section, _ = DiningSection.objects.get_or_create(name="Main Hall")
        for table_name in ["T1", "T2", "T3", "T4"]:
            RestaurantTable.objects.get_or_create(section=section, name=table_name, defaults={"seats": 4})

        starters, _ = MenuCategory.objects.get_or_create(name="Starters", defaults={"color_code": "#dc3545", "sort_order": 1})
        mains, _ = MenuCategory.objects.get_or_create(name="Main Course", defaults={"color_code": "#198754", "sort_order": 2})
        breads, _ = MenuCategory.objects.get_or_create(name="Breads", defaults={"color_code": "#fd7e14", "sort_order": 3})
        beverages, _ = MenuCategory.objects.get_or_create(name="Beverages", defaults={"color_code": "#0dcaf0", "sort_order": 4})

        gram, _ = Unit.objects.get_or_create(name="Gram", short_code="g")
        piece, _ = Unit.objects.get_or_create(name="Piece", short_code="pc", defaults={"allow_decimal": False})
        ml, _ = Unit.objects.get_or_create(name="Millilitre", short_code="ml")

        paneer, _ = Ingredient.objects.get_or_create(name="Paneer", sku="ING-PANEER", defaults={"unit": gram, "current_stock": 5000, "reorder_level": 800})
        yogurt, _ = Ingredient.objects.get_or_create(name="Yogurt", sku="ING-YOGURT", defaults={"unit": gram, "current_stock": 2500, "reorder_level": 500})
        spices, _ = Ingredient.objects.get_or_create(name="Tikka Spice Mix", sku="ING-SPICE", defaults={"unit": gram, "current_stock": 1500, "reorder_level": 300})
        dough, _ = Ingredient.objects.get_or_create(name="Naan Dough", sku="ING-DOUGH", defaults={"unit": piece, "current_stock": 120, "reorder_level": 30})
        soda_base, _ = Ingredient.objects.get_or_create(name="Soft Drink Syrup", sku="ING-SODA", defaults={"unit": ml, "current_stock": 3000, "reorder_level": 500})

        paneer_tikka, _ = MenuItem.objects.get_or_create(
            sku="MENU-PANEER-TIKKA",
            defaults={"category": starters, "tax_rate": gst5, "name": "Paneer Tikka", "base_price": Decimal("260.00")},
        )
        butter_paneer, _ = MenuItem.objects.get_or_create(
            sku="MENU-BUTTER-PANEER",
            defaults={"category": mains, "tax_rate": gst5, "name": "Butter Paneer Masala", "base_price": Decimal("320.00")},
        )
        butter_naan, _ = MenuItem.objects.get_or_create(
            sku="MENU-BUTTER-NAAN",
            defaults={"category": breads, "tax_rate": gst5, "name": "Butter Naan", "base_price": Decimal("45.00")},
        )
        cold_drink, _ = MenuItem.objects.get_or_create(
            sku="MENU-COLA",
            defaults={"category": beverages, "tax_rate": gst5, "name": "Cold Drink", "base_price": Decimal("60.00")},
        )

        recipe, _ = Recipe.objects.get_or_create(menu_item=paneer_tikka, defaults={"yield_quantity": Decimal("1")})
        RecipeLine.objects.get_or_create(recipe=recipe, ingredient=paneer, defaults={"quantity": Decimal("200"), "wastage_percent": Decimal("2")})
        RecipeLine.objects.get_or_create(recipe=recipe, ingredient=yogurt, defaults={"quantity": Decimal("50"), "wastage_percent": Decimal("0")})
        RecipeLine.objects.get_or_create(recipe=recipe, ingredient=spices, defaults={"quantity": Decimal("15"), "wastage_percent": Decimal("5")})

        recipe, _ = Recipe.objects.get_or_create(menu_item=butter_naan, defaults={"yield_quantity": Decimal("1")})
        RecipeLine.objects.get_or_create(recipe=recipe, ingredient=dough, defaults={"quantity": Decimal("1"), "wastage_percent": Decimal("0")})

        recipe, _ = Recipe.objects.get_or_create(menu_item=cold_drink, defaults={"yield_quantity": Decimal("1")})
        RecipeLine.objects.get_or_create(recipe=recipe, ingredient=soda_base, defaults={"quantity": Decimal("250"), "wastage_percent": Decimal("0")})

        Customer.objects.get_or_create(phone_number="9000000001", defaults={"name": "Walk-in Demo"})

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write("Admin login: admin / admin123")
        self.stdout.write("Cashier login: cashier / cash123")
