from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum
from django.shortcuts import render
from django.utils import timezone

from floor.models import RestaurantTable
from inventory.models import Ingredient
from orders.models import Order


@login_required
def dashboard(request):
    today = timezone.localdate()
    today_orders = Order.objects.filter(created_at__date=today, status=Order.Status.COMPLETED)
    context = {
        "today_sales": today_orders.aggregate(total=Sum("total_amount"))["total"] or 0,
        "orders_today": today_orders.count(),
        "open_tables": RestaurantTable.objects.filter(status=RestaurantTable.Status.OCCUPIED).count(),
        "low_stock_items": Ingredient.objects.filter(current_stock__lte=F("reorder_level")).order_by("name")[:8],
        "recent_orders": Order.objects.select_related("table", "customer").order_by("-created_at")[:10],
        "table_status": RestaurantTable.objects.values("status").annotate(total=Count("id")).order_by("status"),
    }
    return render(request, "core/dashboard.html", context)

# Create your views here.
