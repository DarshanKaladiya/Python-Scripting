from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone

from inventory.models import Ingredient, StockLedger
from orders.models import Order


@login_required
def summary_report(request):
    today = timezone.localdate()
    completed_orders = Order.objects.filter(status=Order.Status.COMPLETED)
    context = {
        "today_sales": completed_orders.filter(created_at__date=today).aggregate(total=Sum("total_amount"))["total"] or 0,
        "total_sales": completed_orders.aggregate(total=Sum("total_amount"))["total"] or 0,
        "total_orders": completed_orders.count(),
        "tax_collected": completed_orders.aggregate(total=Sum("tax_amount"))["total"] or 0,
        "low_stock_items": Ingredient.objects.filter(current_stock__lte=F("reorder_level")).order_by("name")[:10],
        "recent_stock_activity": StockLedger.objects.select_related("ingredient")[:10],
    }
    return render(request, "reporting/summary.html", context)

# Create your views here.
