from django.db import transaction

from .models import Ingredient, StockLedger


@transaction.atomic
def create_stock_entry(*, ingredient, txn_type, quantity_change, reference_type="", reference_id=None, notes="", created_by=None, reversal_of=None):
    ingredient = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
    ingredient.current_stock = ingredient.current_stock + quantity_change
    ingredient.save(update_fields=["current_stock"])
    return StockLedger.objects.create(
        ingredient=ingredient,
        txn_type=txn_type,
        quantity_change=quantity_change,
        balance_after=ingredient.current_stock,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
        reversal_of=reversal_of,
        created_by=created_by,
    )
