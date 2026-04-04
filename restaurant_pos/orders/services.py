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


def _invoice_prefix():
    outlet = OutletProfile.objects.first()
    return outlet.invoice_prefix if outlet else "INV"


def _assign_invoice_if_missing(order):
    if order.invoice_number:
        return
    order.invoice_number = next_document_number(_invoice_prefix(), Order.objects.exclude(invoice_number="").count() + 1)


def _finalize_completed_order(*, order, user, update_fields):
    order.recalculate_totals()
    order.status = Order.Status.COMPLETED
    order.updated_by = user
    order.settled_at = timezone.now()
    _assign_invoice_if_missing(order)
    if "subtotal" not in update_fields:
        update_fields.extend(["subtotal", "tax_amount", "total_amount"])
    if "status" not in update_fields:
        update_fields.append("status")
    if "updated_by" not in update_fields:
        update_fields.append("updated_by")
    if "settled_at" not in update_fields:
        update_fields.append("settled_at")
    if "invoice_number" not in update_fields:
        update_fields.append("invoice_number")
    if "updated_at" not in update_fields:
        update_fields.append("updated_at")
    order.save(update_fields=update_fields)
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


def resolve_modifier_selection(*, menu_item, selected_option_ids):
    option_ids = []
    for option_id in selected_option_ids or []:
        if option_id in (None, ""):
            continue
        try:
            option_ids.append(int(option_id))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid modifier option selected.") from exc

    option_ids = list(dict.fromkeys(option_ids))
    groups = list(
        menu_item.modifier_groups.prefetch_related("options").all()
    )
    valid_options = {
        option.id: option
        for group in groups
        for option in group.options.all()
        if option.is_active
    }
    invalid_option_ids = [option_id for option_id in option_ids if option_id not in valid_options]
    if invalid_option_ids:
        raise ValueError("One or more modifier options are not valid for this item.")

    selected_by_group = {}
    for option_id in option_ids:
        option = valid_options[option_id]
        selected_by_group.setdefault(option.group_id, []).append(option)

    snapshot = []
    price_delta_total = Decimal("0")
    for group in groups:
        chosen_options = selected_by_group.get(group.id, [])
        if group.is_required and not chosen_options:
            raise ValueError(f"Please choose an option for {group.name}.")
        if group.selection_type == group.SelectionType.SINGLE and len(chosen_options) > 1:
            raise ValueError(f"Choose only one option for {group.name}.")
        for option in chosen_options:
            snapshot.append(
                {
                    "group_name": group.name,
                    "option_name": option.name,
                    "price_delta": str(option.price_delta),
                }
            )
            price_delta_total += option.price_delta
    return snapshot, price_delta_total


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
def add_item_to_order(*, order, menu_item, quantity=Decimal("1"), notes="", line_discount=Decimal("0"), modifiers=None, modifier_price_delta=Decimal("0")):
    tax_rate = menu_item.tax_rate.rate_percent if menu_item.tax_rate else Decimal("0")
    item = OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        item_name_snapshot=menu_item.name,
        quantity=quantity,
        unit_price=menu_item.base_price + modifier_price_delta,
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
    if order.status not in {Order.Status.COMPLETED, Order.Status.CANCELLED}:
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
    order.save(update_fields=["subtotal", "tax_amount", "total_amount", "payment_status", "updated_at"])
    Payment.objects.filter(order=order).delete()
    for payment in payments:
        Payment.objects.create(
            order=order,
            method=payment["method"],
            amount=payment["amount"],
            reference_number=payment.get("reference_number", ""),
            received_by=user,
        )
    return _finalize_completed_order(order=order, user=user, update_fields=["payment_status"])


@transaction.atomic
def mark_order_paid(*, order, user, payments):
    order.recalculate_totals()
    order.payment_status = Order.PaymentStatus.PAID
    order.updated_by = user
    order.save(update_fields=["subtotal", "tax_amount", "total_amount", "payment_status", "updated_by", "updated_at"])
    Payment.objects.filter(order=order).delete()
    for payment in payments:
        Payment.objects.create(
            order=order,
            method=payment["method"],
            amount=payment["amount"],
            reference_number=payment.get("reference_number", ""),
            received_by=user,
        )
    AuditLog.objects.create(user=user, action="order_paid", entity_type="Order", entity_id=order.id)
    return order


@transaction.atomic
def confirm_self_service_cash_order(*, order, user):
    if order.source != Order.Source.SELF_SERVICE:
        raise ValueError("Only self-service orders can be confirmed here.")
    if order.status != Order.Status.PENDING_CONFIRMATION:
        raise ValueError("This self-service order is not waiting for cashier confirmation.")
    if not order.items.exists():
        raise ValueError("Cannot confirm an empty order.")
    order.updated_by = user
    order.save(update_fields=["updated_by", "updated_at"])
    kot = send_kot(order=order, user=user)
    AuditLog.objects.create(user=user, action="self_service_cash_confirmed", entity_type="Order", entity_id=order.id)
    return kot


@transaction.atomic
def complete_prepaid_order(*, order, user):
    if order.payment_status != Order.PaymentStatus.PAID:
        raise ValueError("Only paid orders can be completed here.")
    if order.status in {Order.Status.COMPLETED, Order.Status.CANCELLED}:
        raise ValueError("This order is already closed.")
    return _finalize_completed_order(order=order, user=user, update_fields=[])


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
        "status_display": order.get_status_display(),
        "payment_status": order.payment_status,
        "payment_status_display": order.get_payment_status_display(),
        "order_type": order.order_type,
        "order_type_display": order.get_order_type_display(),
        "source": order.source,
        "source_display": order.get_source_display(),
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
                "unit_price": str(item.unit_price),
                "status": item.status,
                "notes": item.notes,
                "modifiers": item.modifiers_snapshot,
            }
            for item in order.items.all()
        ],
    }
