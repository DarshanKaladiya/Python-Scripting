from django.db import models


class Recipe(models.Model):
    menu_item = models.OneToOneField("menu.MenuItem", related_name="recipe", on_delete=models.CASCADE)
    yield_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Recipe for {self.menu_item}"


class RecipeLine(models.Model):
    recipe = models.ForeignKey(Recipe, related_name="lines", on_delete=models.CASCADE)
    ingredient = models.ForeignKey("inventory.Ingredient", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    wastage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.ingredient} for {self.recipe.menu_item}"

# Create your models here.
