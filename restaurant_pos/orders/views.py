import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from core.models import PaymentMethod
from customers.models import Customer
from floor.models import RestaurantTable
from menu.models import MenuCategory, MenuItem

from .models import Order
from .services import add_item_to_order, cancel_order, create_order, resolve_modifier_selection, send_kot, serialize_order, settle_order


def _json_body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


@login_required
def pos_screen(request):
    categories = MenuCategory.objects.prefetch_related("items__modifier_groups__options").filter(is_active=True)
    tables = RestaurantTable.objects.filter(is_active=True).select_related("section")
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    active_orders = Order.objects.exclude(status__in=[Order.Status.COMPLETED, Order.Status.CANCELLED])[:10]
    initial_order_id = request.GET.get("order_id", "").strip()
    initial_table_id = request.GET.get("table_id", "").strip()
    menu_item_catalog = {
        item.id: {
            "id": item.id,
            "name": item.name,
            "base_price": str(item.base_price),
            "description": item.description,
            "modifier_groups": [
                {
                    "id": group.id,
                    "name": group.name,
                    "selection_type": group.selection_type,
                    "is_required": group.is_required,
                    "options": [
                        {
                            "id": option.id,
                            "name": option.name,
                            "price_delta": str(option.price_delta),
                        }
                        for option in group.options.all()
                        if option.is_active
                    ],
                }
                for group in item.modifier_groups.all()
            ],
        }
        for category in categories
        for item in category.items.all()
    }
    return render(
        request,
        "orders/pos.html",
        {
            "categories": categories,
            "tables": tables,
            "payment_methods": payment_methods,
            "active_orders": active_orders,
            "initial_order_id": initial_order_id,
            "initial_table_id": initial_table_id,
            "menu_item_catalog": menu_item_catalog,
        },
    )


@login_required
@require_GET
def menu_search(request):
    term = request.GET.get("q", "").strip()
    category_id = request.GET.get("category")
    items = MenuItem.objects.filter(is_active=True)
    if term:
        items = items.filter(name__icontains=term)
    if category_id:
        items = items.filter(category_id=category_id)
    return JsonResponse(
        {
            "results": [
                {
                    "id": item.id,
                    "name": item.name,
                    "price": str(item.base_price),
                    "category": item.category.name,
                }
                for item in items.select_related("category")[:100]
            ]
        }
    )


@login_required
@require_POST
def create_order_api(request):
    payload = _json_body(request)
    table = RestaurantTable.objects.filter(pk=payload.get("table_id")).first()
    customer = None
    phone_number = payload.get("phone_number", "").strip()
    if phone_number:
        customer, _ = Customer.objects.get_or_create(phone_number=phone_number, defaults={"name": payload.get("customer_name", "")})
    order = create_order(
        order_type=payload.get("order_type", Order.OrderType.DINE_IN),
        created_by=request.user,
        table=table,
        customer=customer,
        waiter=request.user if request.user.role == request.user.Role.CAPTAIN else None,
        notes=payload.get("notes", ""),
    )
    return JsonResponse({"order": serialize_order(order)})


@login_required
@require_POST
def add_item_api(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    payload = _json_body(request)
    menu_item = get_object_or_404(MenuItem.objects.prefetch_related("modifier_groups__options"), pk=payload["menu_item_id"])
    try:
        modifier_snapshot, modifier_price_delta = resolve_modifier_selection(
            menu_item=menu_item,
            selected_option_ids=payload.get("modifiers", []),
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    item = add_item_to_order(
        order=order,
        menu_item=menu_item,
        quantity=Decimal(str(payload.get("quantity", "1"))),
        notes=payload.get("notes", ""),
        line_discount=Decimal(str(payload.get("line_discount", "0"))),
        modifiers=modifier_snapshot,
        modifier_price_delta=modifier_price_delta,
    )
    order.refresh_from_db()
    return JsonResponse({"item_id": item.id, "order": serialize_order(order)})


@login_required
@require_POST
def send_kot_api(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    kot = send_kot(order=order, user=request.user)
    order.refresh_from_db()
    return JsonResponse({"kot_number": kot.kot_number if kot else "", "order": serialize_order(order)})


@login_required
@require_POST
def settle_order_api(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    payload = _json_body(request)
    payments = []
    for payment_payload in payload.get("payments", []):
        method = get_object_or_404(PaymentMethod, pk=payment_payload["method_id"])
        payments.append(
            {
                "method": method,
                "amount": Decimal(str(payment_payload["amount"])),
                "reference_number": payment_payload.get("reference_number", ""),
            }
        )
    if not payments:
        raise Http404("At least one payment is required")
    settle_order(order=order, user=request.user, payments=payments)
    order.refresh_from_db()
    return JsonResponse({"order": serialize_order(order)})


@login_required
@require_POST
def hold_order_api(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order.is_held = True
    order.save(update_fields=["is_held"])
    return JsonResponse({"order": serialize_order(order)})


@login_required
@require_POST
def cancel_order_api(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    cancel_order(order=order, user=request.user)
    order.refresh_from_db()
    return JsonResponse({"order": serialize_order(order)})


@login_required
@require_GET
def order_status_api(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=order_id)
    return JsonResponse({"order": serialize_order(order)})


@login_required
def receipt_view(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items", "payments__method"), pk=order_id)
    return render(request, "orders/receipt.html", {"order": order})

# Create your views here.
