import json
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.models import AuditLog, OutletProfile
from customers.models import LoyaltyRule
from inventory.models import StockLedger
from inventory.services import create_stock_entry
from recipes.models import Recipe

from .models import KOTItem, KitchenOrderTicket, Order, OrderItem, Payment


def next_document_number(prefix, count):
    return f"{prefix}{count:05d}"


@transaction.atomic
def create_order(*, order_type, created_by, table=None, customer=None, waiter=None, source=Order.Source.MANUAL, notes=""):
    order = Order.objects.create(
        order_number=next_document_number("ORD", Order.objects.count() + 1),
        order_type=order_type,
        table=table,
        customer=customer,
        waiter=waiter,
        source=source,
        notes=notes,
        created_by=created_by,
        updated_by=created_by,
    )
    if table:
        table.status = table.Status.OCCUPIED
        table.save(update_fields=["status"])
    AuditLog.objects.create(user=created_by, action="order_created", entity_type="Order", entity_id=order.id)
    return order


@transaction.atomic
def add_item_to_order(*, order, menu_item, quantity=Decimal("1"), notes="", line_discount=Decimal("0"), modifiers=None):
    tax_rate = menu_item.tax_rate.rate_percent if menu_item.tax_rate else Decimal("0")
    item = OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        item_name_snapshot=menu_item.name,
        quantity=quantity,
        unit_price=menu_item.base_price,
        line_discount=line_discount,
        tax_rate_snapshot=tax_rate,
        notes=notes,
        modifiers_snapshot=modifiers or [],
    )
    order.recalculate_totals()
    order.save(update_fields=["subtotal", "tax_amount", "total_amount", "updated_at"])
    return item


@transaction.atomic
def send_kot(*, order, user):
    unsent_items = order.items.filter(sent_to_kitchen=False).exclude(status=OrderItem.Status.CANCELLED)
    if not unsent_items.exists():
        return None
    outlet = OutletProfile.objects.first()
    kot_prefix = outlet.kot_prefix if outlet else "KOT"
    kot = KitchenOrderTicket.objects.create(
        order=order,
        kot_number=next_document_number(kot_prefix, KitchenOrderTicket.objects.count() + 1),
        created_by=user,
        source=order.source,
    )
    for item in unsent_items:
        KOTItem.objects.create(kot=kot, order_item=item, quantity=item.quantity)
        item.sent_to_kitchen = True
        item.save(update_fields=["sent_to_kitchen"])
    order.status = Order.Status.KOT_SENT
    order.updated_by = user
    order.save(update_fields=["status", "updated_by", "updated_at"])
    AuditLog.objects.create(user=user, action="kot_sent", entity_type="Order", entity_id=order.id, payload={"kot_id": kot.id})
    return kot


@transaction.atomic
def apply_recipe_deductions(*, order, user=None):
    if order.stock_posted:
        return
    for item in order.items.exclude(status=OrderItem.Status.CANCELLED):
        if not item.menu_item.track_inventory:
            continue
        recipe = Recipe.objects.filter(menu_item=item.menu_item, is_active=True).prefetch_related("lines__ingredient").first()
        if not recipe:
            continue
        for line in recipe.lines.all():
            qty = (line.quantity * item.quantity) * (Decimal("1") + (line.wastage_percent / Decimal("100")))
            create_stock_entry(
                ingredient=line.ingredient,
                txn_type=StockLedger.TxnType.SALE_DEDUCTION,
                quantity_change=-qty,
                reference_type="order",
                reference_id=order.id,
                notes=f"Sold via order {order.order_number}",
                created_by=user,
            )
    order.stock_posted = True
    order.save(update_fields=["stock_posted"])


@transaction.atomic
def reverse_recipe_deductions(*, order, user=None):
    ledger_entries = list(StockLedger.objects.filter(reference_type="order", reference_id=order.id, txn_type=StockLedger.TxnType.SALE_DEDUCTION))
    for entry in ledger_entries:
        create_stock_entry(
            ingredient=entry.ingredient,
            txn_type=StockLedger.TxnType.REVERSAL,
            quantity_change=-entry.quantity_change,
            reference_type="order_cancel",
            reference_id=order.id,
            notes=f"Reversal for order {order.order_number}",
            created_by=user,
            reversal_of=entry,
        )
    order.stock_posted = False
    order.save(update_fields=["stock_posted"])


@transaction.atomic
def settle_order(*, order, user, payments):
    order.recalculate_totals()
    order.payment_status = Order.PaymentStatus.PAID
    order.status = Order.Status.COMPLETED
    order.updated_by = user
    order.settled_at = timezone.now()
    outlet = OutletProfile.objects.first()
    invoice_prefix = outlet.invoice_prefix if outlet else "INV"
    if not order.invoice_number:
        order.invoice_number = next_document_number(invoice_prefix, Order.objects.exclude(invoice_number="").count() + 1)
    order.save(update_fields=["subtotal", "tax_amount", "total_amount", "payment_status", "status", "updated_by", "settled_at", "invoice_number", "updated_at"])
    Payment.objects.filter(order=order).delete()
    for payment in payments:
        Payment.objects.create(
            order=order,
            method=payment["method"],
            amount=payment["amount"],
            reference_number=payment.get("reference_number", ""),
            received_by=user,
        )
    if order.table:
        order.table.status = order.table.Status.AVAILABLE
        order.table.save(update_fields=["status"])
    apply_recipe_deductions(order=order, user=user)
    if order.customer:
        loyalty_rule = LoyaltyRule.objects.first()
        if loyalty_rule:
            points = order.total_amount * loyalty_rule.points_per_rupee
            order.customer.add_points(points)
    AuditLog.objects.create(user=user, action="order_settled", entity_type="Order", entity_id=order.id)
    return order


@transaction.atomic
def cancel_order(*, order, user):
    if order.stock_posted:
        reverse_recipe_deductions(order=order, user=user)
    order.status = Order.Status.CANCELLED
    order.payment_status = Order.PaymentStatus.REFUNDED if order.payments.exists() else Order.PaymentStatus.UNPAID
    order.updated_by = user
    order.save(update_fields=["status", "payment_status", "updated_by", "updated_at"])
    if order.table:
        order.table.status = order.table.Status.AVAILABLE
        order.table.save(update_fields=["status"])
    AuditLog.objects.create(user=user, action="order_cancelled", entity_type="Order", entity_id=order.id)
    return order


def serialize_order(order):
    return {
        "id": order.id,
        "order_number": order.order_number,
        "invoice_number": order.invoice_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "order_type": order.order_type,
        "subtotal": str(order.subtotal),
        "tax_amount": str(order.tax_amount),
        "discount_amount": str(order.discount_amount),
        "total_amount": str(order.total_amount),
        "table_id": order.table_id,
        "table": order.table.name if order.table else "",
        "customer_phone": order.customer.phone_number if order.customer else "",
        "customer_name": order.customer.name if order.customer else "",
        "items": [
            {
                "id": item.id,
                "name": item.item_name_snapshot,
                "quantity": str(item.quantity),
                "price": str(item.total_price),
                "status": item.status,
                "notes": item.notes,
                "modifiers": json.dumps(item.modifiers_snapshot),
            }
            for item in order.items.all()
        ],
    }
