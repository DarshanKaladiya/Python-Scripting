from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from floor.models import RestaurantTable
from inventory.models import Ingredient
from orders.models import Order


def _serialize_recent_order(order):
    return {
        "order_number": order.order_number,
        "order_type_display": order.get_order_type_display(),
        "table_name": order.table.name if order.table else "Walk-in",
        "status": order.status,
        "status_display": order.get_status_display(),
        "total_amount": str(order.total_amount),
        "created_time": timezone.localtime(order.created_at).strftime("%H:%M"),
    }


def _serialize_table_status(row):
    return {
        "status": row["status"],
        "status_display": row["status"].title(),
        "total": row["total"],
    }


def _serialize_low_stock_item(ingredient):
    return {
        "name": ingredient.name,
        "sku": ingredient.sku,
        "current_stock": str(ingredient.current_stock),
        "reorder_level": str(ingredient.reorder_level),
        "unit": ingredient.unit.short_code,
    }


def _dashboard_summary():
    today = timezone.localdate()
    today_orders = Order.objects.filter(created_at__date=today, status=Order.Status.COMPLETED)
    low_stock_qs = Ingredient.objects.filter(current_stock__lte=F("reorder_level")).select_related("unit").order_by("name")
    recent_orders_qs = Order.objects.select_related("table", "customer").order_by("-created_at")[:10]
    table_status_qs = RestaurantTable.objects.values("status").annotate(total=Count("id")).order_by("status")
    return {
        "today_sales": today_orders.aggregate(total=Sum("total_amount"))["total"] or 0,
        "orders_today": today_orders.count(),
        "open_tables": RestaurantTable.objects.filter(status=RestaurantTable.Status.OCCUPIED).count(),
        "low_stock_count": low_stock_qs.count(),
        "low_stock_items": list(low_stock_qs[:8]),
        "recent_orders": list(recent_orders_qs),
        "table_status": list(table_status_qs),
    }


@login_required
def dashboard(request):
    summary = _dashboard_summary()
    context = {
        "today_sales": summary["today_sales"],
        "orders_today": summary["orders_today"],
        "open_tables": summary["open_tables"],
        "low_stock_items": summary["low_stock_items"],
        "recent_orders": summary["recent_orders"],
        "table_status": summary["table_status"],
    }
    return render(request, "core/dashboard.html", context)


@login_required
def dashboard_summary_api(request):
    summary = _dashboard_summary()
    return JsonResponse(
        {
            "today_sales": str(summary["today_sales"]),
            "orders_today": summary["orders_today"],
            "open_tables": summary["open_tables"],
            "low_stock_count": summary["low_stock_count"],
            "recent_orders": [_serialize_recent_order(order) for order in summary["recent_orders"]],
            "table_status": [_serialize_table_status(row) for row in summary["table_status"]],
            "low_stock_items": [_serialize_low_stock_item(item) for item in summary["low_stock_items"]],
        }
    )
