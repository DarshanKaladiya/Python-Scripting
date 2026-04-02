from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Customer


@login_required
def lookup_customer(request):
    phone_number = request.GET.get("phone", "").strip()
    if not phone_number:
        return JsonResponse({"error": "phone is required"}, status=400)

    customer, _ = Customer.objects.get_or_create(phone_number=phone_number)
    return JsonResponse(
        {
            "id": customer.id,
            "name": customer.name,
            "phone_number": customer.phone_number,
            "loyalty_points": str(customer.loyalty_points),
        }
    )

# Create your views here.
