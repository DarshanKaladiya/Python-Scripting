import json

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from menu.models import MenuItem
from orders.models import Order
from orders.services import add_item_to_order, create_order, send_kot

from .models import ExternalOrder


@csrf_exempt
@require_POST
@transaction.atomic
def provider_order_webhook(request, provider):
    payload = json.loads(request.body.decode("utf-8") or "{}")
    external_order_id = str(payload.get("order_id") or payload.get("external_order_id") or "")
    if not external_order_id:
        return JsonResponse({"error": "order_id is required"}, status=400)

    source = provider.lower()
    idempotency_key = payload.get("idempotency_key") or f"{source}:{external_order_id}"
    external_order, created = ExternalOrder.objects.get_or_create(
        idempotency_key=idempotency_key,
        defaults={
            "source": source,
            "external_order_id": external_order_id,
            "payload_snapshot": payload,
        },
    )
    if not created:
        return JsonResponse({"external_order_id": external_order.id, "duplicate": True, "order_id": external_order.order_id})

    order = create_order(order_type=Order.OrderType.DELIVERY, created_by=None, source=source, notes=f"{provider.title()} order")
    mapped_items = []
    for line in payload.get("items", []):
        menu_item = MenuItem.objects.filter(name__iexact=line.get("name", "")).first()
        if not menu_item:
            continue
        add_item_to_order(order=order, menu_item=menu_item, quantity=line.get("quantity", 1))
        mapped_items.append({"menu_item_id": menu_item.id, "name": menu_item.name})
    send_kot(order=order, user=None)
    external_order.order = order
    external_order.mapped_items = mapped_items
    external_order.sync_status = ExternalOrder.SyncStatus.PROCESSED
    external_order.save(update_fields=["order", "mapped_items", "sync_status"])
    return JsonResponse({"external_order_id": external_order.id, "duplicate": False, "order_id": order.id})

# Create your views here.
