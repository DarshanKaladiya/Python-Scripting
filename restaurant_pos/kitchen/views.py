import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from orders.models import KOTItem, KitchenOrderTicket, Order, OrderItem


@login_required
def kds_screen(request):
    lane_config = [
        {
            "key": KitchenOrderTicket.Status.NEW,
            "label": "New",
            "description": "Freshly fired items waiting to be picked up by the line.",
        },
        {
            "key": KitchenOrderTicket.Status.PREPARING,
            "label": "Preparing",
            "description": "Items that are actively on the stove, grill, or assembly station.",
        },
        {
            "key": KitchenOrderTicket.Status.READY,
            "label": "Ready",
            "description": "Finished items waiting for handoff to service.",
        },
    ]
    kot_items = list(
        KOTItem.objects.select_related("kot", "order_item", "kot__order", "kot__order__table")
        .exclude(status=KitchenOrderTicket.Status.SERVED)
        .order_by("status", "kot__created_at", "id")
    )
    items_by_status = {lane["key"]: [] for lane in lane_config}
    for item in kot_items:
        items_by_status.setdefault(item.status, []).append(item)
    lanes = [
        {
            **lane,
            "items": items_by_status.get(lane["key"], []),
        }
        for lane in lane_config
    ]
    context = {
        "lanes": lanes,
        "active_item_count": len(kot_items),
        "active_ticket_count": len({item.kot_id for item in kot_items}),
    }
    return render(request, "kitchen/kds.html", context)


@login_required
@require_POST
def update_item_status(request, kot_item_id):
    payload = json.loads(request.body.decode("utf-8") or "{}")
    kot_item = get_object_or_404(KOTItem, pk=kot_item_id)
    new_status = payload.get("status", KitchenOrderTicket.Status.PREPARING)
    kot_item.status = new_status
    kot_item.save(update_fields=["status"])
    kot_item.order_item.status = {
        KitchenOrderTicket.Status.NEW: OrderItem.Status.PENDING,
        KitchenOrderTicket.Status.PREPARING: OrderItem.Status.PREPARING,
        KitchenOrderTicket.Status.READY: OrderItem.Status.READY,
        KitchenOrderTicket.Status.SERVED: OrderItem.Status.SERVED,
    }[new_status]
    kot_item.order_item.save(update_fields=["status"])
    order = kot_item.kot.order
    if order.items.filter(status=OrderItem.Status.READY).exists():
        order.status = Order.Status.READY
        order.save(update_fields=["status"])
    return JsonResponse({"status": kot_item.status})

# Create your views here.
