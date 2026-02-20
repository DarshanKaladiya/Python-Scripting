from django.shortcuts import render
from .utils import get_medicine_prices

def home(request):
    return render(request, 'comparison/index.html')

def search_medicine(request):
    if request.method == "POST":
        medicine_name = request.POST.get('medicine_name')
        results = get_medicine_prices(medicine_name)

        valid_prices = [res['price'] for res in results if isinstance(res['price'], int)]
        cheapest_price = min(valid_prices) if valid_prices else None
        max_price = max(valid_prices) if valid_prices else None

        for res in results:
            if res['price'] and max_price and max_price > res['price']:
                savings = ((max_price - res['price']) / max_price) * 100
                res['savings_percent'] = round(savings)
            else:
                res['savings_percent'] = 0

        context = {
            'medicine': medicine_name.upper(),
            'results': results,
            'cheapest_price': cheapest_price,
        }
        return render(request, 'comparison/results.html', context)
    
    return render(request, 'comparison/index.html')