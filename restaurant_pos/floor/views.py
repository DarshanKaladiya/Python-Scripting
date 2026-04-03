from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from orders.models import Order
from orders.services import create_order

from .models import DiningSection, RestaurantTable


ACTIVE_ORDER_EXCLUDES = [Order.Status.COMPLETED, Order.Status.CANCELLED]
OPENABLE_TABLE_STATUSES = {RestaurantTable.Status.AVAILABLE, RestaurantTable.Status.RESERVED}


def _active_dine_in_orders():
    return (
        Order.objects.exclude(status__in=ACTIVE_ORDER_EXCLUDES)
        .filter(table__isnull=False, order_type=Order.OrderType.DINE_IN)
        .select_related("table", "customer")
        .order_by("-created_at")
    )


@login_required
def table_management_screen(request):
    sections = DiningSection.objects.prefetch_related("tables").order_by("name")
    active_orders = list(_active_dine_in_orders())
    active_orders_by_table = {}
    for order in active_orders:
        active_orders_by_table.setdefault(order.table_id, order)

    transfer_targets = [
        table
        for table in RestaurantTable.objects.filter(is_active=True).select_related("section").order_by("section__name", "name")
        if table.status in OPENABLE_TABLE_STATUSES and table.id not in active_orders_by_table
    ]

    section_cards = []
    for section in sections:
        table_cards = []
        for table in section.tables.all():
            if not table.is_active:
                continue
            active_order = active_orders_by_table.get(table.id)
            table_cards.append(
                {
                    "table": table,
                    "active_order": active_order,
                    "can_open_order": table.status in OPENABLE_TABLE_STATUSES and not active_order,
                    "transfer_targets": [target for target in transfer_targets if target.id != table.id],
                }
            )
        section_cards.append(
            {
                "section": section,
                "tables": table_cards,
                "occupied_count": sum(1 for card in table_cards if card["table"].status == RestaurantTable.Status.OCCUPIED),
            }
        )
    all_cards = [card for section in section_cards for card in section["tables"]]

    context = {
        "sections": section_cards,
        "active_table_orders": len(active_orders),
        "available_tables": sum(1 for card in all_cards if card["table"].status == RestaurantTable.Status.AVAILABLE),
        "occupied_tables": sum(1 for card in all_cards if card["table"].status == RestaurantTable.Status.OCCUPIED),
    }
    return render(request, "floor/management.html", context)


@login_required
@require_POST
def open_table_order(request, table_id):
    table = get_object_or_404(RestaurantTable.objects.select_related("section"), pk=table_id, is_active=True)
    existing_order = _active_dine_in_orders().filter(table=table).first()
    if existing_order:
        messages.info(request, f"{table.section.name} {table.name} already has an active order open.")
        return redirect(f"{reverse('orders:pos')}?order_id={existing_order.id}")
    if table.status not in OPENABLE_TABLE_STATUSES:
        messages.error(request, f"{table.section.name} {table.name} is not ready for a new dine-in order.")
        return redirect("floor:management")

    order = create_order(
        order_type=Order.OrderType.DINE_IN,
        created_by=request.user,
        table=table,
        waiter=request.user if request.user.role == request.user.Role.CAPTAIN else None,
    )
    messages.success(request, f"Started {order.order_number} for {table.section.name} {table.name}.")
    return redirect(f"{reverse('orders:pos')}?order_id={order.id}")


@login_required
@require_POST
def transfer_table_order(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("table", "table__section"),
        pk=order_id,
        order_type=Order.OrderType.DINE_IN,
    )
    if order.status in ACTIVE_ORDER_EXCLUDES or not order.table_id:
        messages.error(request, "Only active dine-in orders with a table can be transferred.")
        return redirect("floor:management")

    target_table = get_object_or_404(
        RestaurantTable.objects.select_related("section"),
        pk=request.POST.get("target_table_id"),
        is_active=True,
    )
    if target_table.id == order.table_id:
        messages.info(request, "That order is already assigned to the selected table.")
        return redirect("floor:management")
    if target_table.status not in OPENABLE_TABLE_STATUSES:
        messages.error(request, f"{target_table.section.name} {target_table.name} is not available for transfer.")
        return redirect("floor:management")
    if _active_dine_in_orders().filter(table=target_table).exists():
        messages.error(request, f"{target_table.section.name} {target_table.name} already has an active order.")
        return redirect("floor:management")

    source_table = order.table
    order.table = target_table
    order.updated_by = request.user
    order.save(update_fields=["table", "updated_by", "updated_at"])

    target_table.status = RestaurantTable.Status.OCCUPIED
    target_table.save(update_fields=["status"])
    source_table.status = RestaurantTable.Status.AVAILABLE
    source_table.save(update_fields=["status"])

    messages.success(
        request,
        f"Moved {order.order_number} from {source_table.section.name} {source_table.name} to {target_table.section.name} {target_table.name}.",
    )
    return redirect("floor:management")
