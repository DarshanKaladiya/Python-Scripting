from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import OutletProfile, PaymentMethod, TaxRate
from customers.models import Customer, LoyaltyRule
from floor.models import DiningSection, RestaurantTable
from inventory.models import Ingredient, Unit
from menu.models import MenuCategory, MenuItem, ModifierGroup, ModifierOption
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
        rice, _ = MenuCategory.objects.get_or_create(name="Rice & Biryani", defaults={"color_code": "#8b5cf6", "sort_order": 5})
        desserts, _ = MenuCategory.objects.get_or_create(name="Desserts", defaults={"color_code": "#ec4899", "sort_order": 6})
        soups, _ = MenuCategory.objects.get_or_create(name="Soups", defaults={"color_code": "#f59e0b", "sort_order": 7})

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

        menu_items = [
            {
                "sku": "MENU-HARA-BHARA",
                "category": starters,
                "name": "Hara Bhara Kebab",
                "base_price": Decimal("220.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "HB Kebab",
                "description": "Spinach and green pea kebabs served with mint chutney.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-VEG-MANCHURIAN",
                "category": starters,
                "name": "Veg Manchurian Dry",
                "base_price": Decimal("240.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Veg Manch",
                "description": "Crispy vegetable dumplings tossed with Indo-Chinese sauce.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-CHILLI-PANEER",
                "category": starters,
                "name": "Chilli Paneer",
                "base_price": Decimal("280.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Chilli Pan",
                "description": "Paneer cubes sauteed with capsicum, onion, and chilli sauce.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-DAL-MAKHANI",
                "category": mains,
                "name": "Dal Makhani",
                "base_price": Decimal("260.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Dal Mak",
                "description": "Slow-cooked black lentils finished with butter and cream.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-KADAI-PANEER",
                "category": mains,
                "name": "Kadai Paneer",
                "base_price": Decimal("310.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Kadai Pan",
                "description": "Paneer cooked with onion, capsicum, and roasted kadai masala.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-VEG-KOLHAPURI",
                "category": mains,
                "name": "Veg Kolhapuri",
                "base_price": Decimal("290.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Veg Kolh",
                "description": "Mixed vegetables in a spicy Maharashtrian-style gravy.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-TANDOORI-ROTI",
                "category": breads,
                "name": "Tandoori Roti",
                "base_price": Decimal("35.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Tand Roti",
                "description": "Classic whole wheat roti baked in the tandoor.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-GARLIC-NAAN",
                "category": breads,
                "name": "Garlic Naan",
                "base_price": Decimal("65.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Gar Naan",
                "description": "Soft naan topped with garlic and coriander butter.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-LACCHA-PARATHA",
                "category": breads,
                "name": "Laccha Paratha",
                "base_price": Decimal("70.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Laccha",
                "description": "Layered flaky paratha finished on the tawa.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-JEERA-RICE",
                "category": rice,
                "name": "Jeera Rice",
                "base_price": Decimal("160.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Jeera Rice",
                "description": "Fragrant basmati rice tempered with cumin and ghee.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-VEG-PULAO",
                "category": rice,
                "name": "Veg Pulao",
                "base_price": Decimal("210.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Veg Pulao",
                "description": "Basmati rice tossed with vegetables and mild spices.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-PANEER-BIRYANI",
                "category": rice,
                "name": "Paneer Biryani",
                "base_price": Decimal("330.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Pan Biry",
                "description": "Layered dum biryani with paneer tikka and aromatic rice.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-TOMATO-SOUP",
                "category": soups,
                "name": "Tomato Soup",
                "base_price": Decimal("120.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Tom Soup",
                "description": "Creamy tomato soup served hot with croutons.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-SWEET-CORN",
                "category": soups,
                "name": "Sweet Corn Soup",
                "base_price": Decimal("130.00"),
                "item_type": MenuItem.ItemType.VEG,
                "short_name": "Corn Soup",
                "description": "Sweet corn soup with vegetables and spring onion.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-BROWNIE",
                "category": desserts,
                "name": "Sizzling Brownie",
                "base_price": Decimal("190.00"),
                "item_type": MenuItem.ItemType.OTHER,
                "short_name": "Brownie",
                "description": "Warm chocolate brownie served with vanilla ice cream.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-GULAB-JAMUN",
                "category": desserts,
                "name": "Gulab Jamun",
                "base_price": Decimal("110.00"),
                "item_type": MenuItem.ItemType.OTHER,
                "short_name": "Jamun",
                "description": "Soft milk dumplings soaked in cardamom sugar syrup.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-KULFI",
                "category": desserts,
                "name": "Malai Kulfi",
                "base_price": Decimal("120.00"),
                "item_type": MenuItem.ItemType.OTHER,
                "short_name": "Kulfi",
                "description": "Traditional dense Indian ice cream with pistachio garnish.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-MASALA-COLA",
                "category": beverages,
                "name": "Masala Cola",
                "base_price": Decimal("75.00"),
                "item_type": MenuItem.ItemType.BEVERAGE,
                "short_name": "Masala Cola",
                "description": "Chilled cola finished with chat masala and lemon.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-LIME-SODA",
                "category": beverages,
                "name": "Fresh Lime Soda",
                "base_price": Decimal("85.00"),
                "item_type": MenuItem.ItemType.BEVERAGE,
                "short_name": "Lime Soda",
                "description": "Refreshing sweet-and-salt lime soda.",
                "track_inventory": False,
            },
            {
                "sku": "MENU-COLD-COFFEE",
                "category": beverages,
                "name": "Cold Coffee",
                "base_price": Decimal("140.00"),
                "item_type": MenuItem.ItemType.BEVERAGE,
                "short_name": "Cold Coffee",
                "description": "Chilled creamy coffee blended with ice cream.",
                "track_inventory": False,
            },
        ]

        for item_data in menu_items:
            MenuItem.objects.get_or_create(
                sku=item_data["sku"],
                defaults={
                    "category": item_data["category"],
                    "tax_rate": gst5,
                    "name": item_data["name"],
                    "base_price": item_data["base_price"],
                    "item_type": item_data["item_type"],
                    "short_name": item_data["short_name"],
                    "description": item_data["description"],
                    "track_inventory": item_data["track_inventory"],
                },
            )

        spice_level, _ = ModifierGroup.objects.get_or_create(
            name="Spice Level",
            defaults={"selection_type": ModifierGroup.SelectionType.SINGLE, "is_required": True},
        )
        extra_addons, _ = ModifierGroup.objects.get_or_create(
            name="Add-ons",
            defaults={"selection_type": ModifierGroup.SelectionType.MULTIPLE, "is_required": False},
        )
        preparation, _ = ModifierGroup.objects.get_or_create(
            name="Preparation Style",
            defaults={"selection_type": ModifierGroup.SelectionType.SINGLE, "is_required": False},
        )
        beverage_size, _ = ModifierGroup.objects.get_or_create(
            name="Beverage Size",
            defaults={"selection_type": ModifierGroup.SelectionType.SINGLE, "is_required": True},
        )
        beverage_preferences, _ = ModifierGroup.objects.get_or_create(
            name="Beverage Preferences",
            defaults={"selection_type": ModifierGroup.SelectionType.MULTIPLE, "is_required": False},
        )

        modifier_options = [
            (spice_level, "Mild", Decimal("0.00")),
            (spice_level, "Medium", Decimal("0.00")),
            (spice_level, "Spicy", Decimal("0.00")),
            (extra_addons, "Extra Butter", Decimal("20.00")),
            (extra_addons, "Extra Cheese", Decimal("40.00")),
            (extra_addons, "Extra Paneer", Decimal("55.00")),
            (preparation, "Regular", Decimal("0.00")),
            (preparation, "Jain", Decimal("25.00")),
            (preparation, "Less Oil", Decimal("0.00")),
            (beverage_size, "Regular", Decimal("0.00")),
            (beverage_size, "Large", Decimal("30.00")),
            (beverage_preferences, "Less Ice", Decimal("0.00")),
            (beverage_preferences, "No Sugar", Decimal("0.00")),
        ]
        for group, name, price_delta in modifier_options:
            ModifierOption.objects.get_or_create(
                group=group,
                name=name,
                defaults={"price_delta": price_delta},
            )

        modifier_map = {
            "MENU-PANEER-TIKKA": [spice_level, extra_addons, preparation],
            "MENU-CHILLI-PANEER": [spice_level, extra_addons, preparation],
            "MENU-KADAI-PANEER": [spice_level, extra_addons, preparation],
            "MENU-PANEER-BIRYANI": [spice_level, extra_addons, preparation],
            "MENU-COLA": [beverage_size, beverage_preferences],
            "MENU-MASALA-COLA": [beverage_size, beverage_preferences],
            "MENU-LIME-SODA": [beverage_size, beverage_preferences],
            "MENU-COLD-COFFEE": [beverage_size, beverage_preferences],
        }
        for sku, groups in modifier_map.items():
            menu_item = MenuItem.objects.filter(sku=sku).first()
            if menu_item:
                menu_item.modifier_groups.add(*groups)

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
