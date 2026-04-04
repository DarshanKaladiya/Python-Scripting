import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from core.models import PaymentMethod
from customers.models import Customer
from floor.models import RestaurantTable
from menu.models import MenuCategory, MenuItem

from .models import Order
from .services import (
    add_item_to_order,
    cancel_order,
    complete_prepaid_order,
    confirm_self_service_cash_order,
    create_order,
    mark_order_paid,
    resolve_modifier_selection,
    send_kot,
    serialize_order,
    settle_order,
)


ACTIVE_ORDER_EXCLUDES = [Order.Status.COMPLETED, Order.Status.CANCELLED]


def _json_body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _menu_catalog(categories):
    return {
        item.id: {
            "id": item.id,
            "name": item.name,
            "base_price": str(item.base_price),
            "tax_rate": str(item.tax_rate.rate_percent if item.tax_rate else "0"),
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


def _resolve_customer(payload):
    phone_number = payload.get("phone_number", "").strip()
    if not phone_number:
        return None
    customer, _ = Customer.objects.get_or_create(
        phone_number=phone_number,
        defaults={"name": payload.get("customer_name", "").strip()},
    )
    if payload.get("customer_name", "").strip() and customer.name != payload.get("customer_name", "").strip():
        customer.name = payload.get("customer_name", "").strip()
        customer.save(update_fields=["name"])
    return customer


def _validate_self_service_table(order_type, table):
    if order_type != Order.OrderType.DINE_IN:
        return
    if not table:
        raise ValueError("Please choose a table for dine-in self ordering.")
    if table.status not in {RestaurantTable.Status.AVAILABLE, RestaurantTable.Status.RESERVED}:
        raise ValueError("That table is not currently open for a new self-order.")
    active_table_order_exists = (
        Order.objects.exclude(status__in=ACTIVE_ORDER_EXCLUDES)
        .filter(order_type=Order.OrderType.DINE_IN, table=table)
        .exists()
    )
    if active_table_order_exists:
        raise ValueError("That table already has an active order.")


def _self_service_response(order, *, direct_to_kitchen):
    return JsonResponse(
        {
            "order": serialize_order(order),
            "direct_to_kitchen": direct_to_kitchen,
            "message": (
                "Payment received. Your order has been sent to the kitchen."
                if direct_to_kitchen
                else "Your order is waiting for cashier confirmation before it reaches the kitchen."
            ),
        }
    )


@login_required
def pos_screen(request):
    categories = MenuCategory.objects.prefetch_related("items__modifier_groups__options").filter(is_active=True)
    tables = RestaurantTable.objects.filter(is_active=True).select_related("section")
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    active_orders = (
        Order.objects.exclude(status__in=ACTIVE_ORDER_EXCLUDES)
        .exclude(status=Order.Status.PENDING_CONFIRMATION, source=Order.Source.SELF_SERVICE)
        .select_related("table", "customer")
        [:10]
    )
    pending_self_orders = (
        Order.objects.filter(status=Order.Status.PENDING_CONFIRMATION, source=Order.Source.SELF_SERVICE)
        .select_related("table", "customer")
        .prefetch_related("items")
        .order_by("created_at")
    )
    initial_order_id = request.GET.get("order_id", "").strip()
    initial_table_id = request.GET.get("table_id", "").strip()
    menu_item_catalog = _menu_catalog(categories)
    return render(
        request,
        "orders/pos.html",
        {
            "categories": categories,
            "tables": tables,
            "payment_methods": payment_methods,
            "active_orders": active_orders,
            "pending_self_orders": pending_self_orders,
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
    customer = _resolve_customer(payload)
    order = create_order(
        order_type=payload.get("order_type", Order.OrderType.DINE_IN),
        created_by=request.user,
        table=table,
        customer=customer,
        waiter=request.user if request.user.role == request.user.Role.CAPTAIN else None,
        notes=payload.get("notes", ""),
    )
    return JsonResponse({"order": serialize_order(order)})


def self_service_screen(request):
    categories = MenuCategory.objects.prefetch_related("items__modifier_groups__options").filter(is_active=True)
    tables = RestaurantTable.objects.filter(
        is_active=True,
        status__in=[RestaurantTable.Status.AVAILABLE, RestaurantTable.Status.RESERVED],
    ).select_related("section")
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    return render(
        request,
        "orders/self_service.html",
        {
            "categories": categories,
            "tables": tables,
            "payment_methods": payment_methods,
            "menu_item_catalog": _menu_catalog(categories),
        },
    )


@require_POST
def submit_self_service_order_api(request):
    payload = _json_body(request)
    items_payload = payload.get("items", [])
    if not items_payload:
        return JsonResponse({"error": "Add at least one item before placing the order."}, status=400)

    order_type = payload.get("order_type", Order.OrderType.TAKEAWAY)
    table = RestaurantTable.objects.filter(pk=payload.get("table_id"), is_active=True).select_related("section").first()
    try:
        _validate_self_service_table(order_type, table)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    payment_method = get_object_or_404(PaymentMethod.objects.filter(is_active=True), pk=payload.get("payment_method_id"))
    customer = _resolve_customer(payload)
    original_table_status = table.status if table else None
    order = create_order(
        order_type=order_type,
        created_by=None,
        table=table if order_type == Order.OrderType.DINE_IN else None,
        customer=customer,
        source=Order.Source.SELF_SERVICE,
        notes=payload.get("notes", "").strip(),
    )

    try:
        for item_payload in items_payload:
            menu_item = get_object_or_404(
                MenuItem.objects.prefetch_related("modifier_groups__options"),
                pk=item_payload["menu_item_id"],
                is_active=True,
            )
            modifier_snapshot, modifier_price_delta = resolve_modifier_selection(
                menu_item=menu_item,
                selected_option_ids=item_payload.get("modifiers", []),
            )
            add_item_to_order(
                order=order,
                menu_item=menu_item,
                quantity=Decimal(str(item_payload.get("quantity", "1"))),
                notes=item_payload.get("notes", "").strip(),
                line_discount=Decimal("0"),
                modifiers=modifier_snapshot,
                modifier_price_delta=modifier_price_delta,
            )
    except (KeyError, ValueError) as exc:
        if table and original_table_status:
            table.status = original_table_status
            table.save(update_fields=["status"])
        order.delete()
        return JsonResponse({"error": str(exc)}, status=400)

    order.refresh_from_db()
    if payment_method.is_cash:
        order.status = Order.Status.PENDING_CONFIRMATION
        order.save(update_fields=["status", "updated_at"])
        return _self_service_response(order, direct_to_kitchen=False)

    mark_order_paid(
        order=order,
        user=None,
        payments=[
            {
                "method": payment_method,
                "amount": order.total_amount,
                "reference_number": f"SELF-{payment_method.code.upper()}-{order.order_number}",
            }
        ],
    )
    send_kot(order=order, user=None)
    order.refresh_from_db()
    return _self_service_response(order, direct_to_kitchen=True)


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


@login_required
@require_POST
def confirm_self_service_cash_order_view(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "table", "customer"),
        pk=order_id,
        source=Order.Source.SELF_SERVICE,
    )
    try:
        kot = confirm_self_service_cash_order(order=order, user=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("orders:pos")

    if kot:
        messages.success(request, f"{order.order_number} confirmed and sent to the kitchen as {kot.kot_number}.")
    else:
        messages.info(request, f"{order.order_number} is already fully synced with the kitchen.")
    return redirect(f"{reverse('orders:pos')}?order_id={order.id}")


@login_required
@require_POST
def complete_prepaid_order_view(request, order_id):
    order = get_object_or_404(Order.objects.select_related("table", "customer"), pk=order_id)
    try:
        complete_prepaid_order(order=order, user=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("orders:pos")

    messages.success(request, f"{order.order_number} has been completed without taking payment again.")
    return redirect("orders:pos")
