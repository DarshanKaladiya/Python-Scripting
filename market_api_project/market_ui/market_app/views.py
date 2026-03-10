import requests
from django.shortcuts import render

def price_comparison_chart(request):
    all_districts = ['Ahmedabad', 'Gondal', 'Rajkot']
    commodity = request.GET.get('commodity', 'Cotton')
    s_year = request.GET.get('start_year', 2021)
    e_year = request.GET.get('end_year', 2026)
    selected_districts = request.GET.getlist('districts')
    
    if not selected_districts:
        selected_districts = all_districts

    dist_query = "&".join([f"district={d}" for d in selected_districts])
    api_url = f"http://127.0.0.1:8000/api/search/?commodity={commodity}&start_year={s_year}&end_year={e_year}&{dist_query}"
    
    chart_data = {}
    summary_stats = []
    arbitrage = None

    try:
        response = requests.get(api_url)
        all_records = response.json().get('data', [])

        recent_prices = []
        for d in selected_districts:
            # Filter and Sort by date
            dist_records = [i for i in all_records if i['district_name'] == d]
            dist_records.sort(key=lambda x: x['price_date'])
            chart_data[d] = dist_records
            
            if dist_records:
                prices = [r['average_price'] for r in dist_records]
                last_p = prices[-1]
                recent_prices.append({'district': d, 'price': last_p})
                
                summary_stats.append({
                    'district': d,
                    'avg': round(sum(prices) / len(prices), 2),
                    'max': max(prices),
                    'min': min(prices),
                    'last': last_p
                })

        if len(recent_prices) >= 2:
            sorted_r = sorted(recent_prices, key=lambda x: x['price'])
            arbitrage = {'buy': sorted_r[0]['district'], 'sell': sorted_r[-1]['district'], 'profit': sorted_r[-1]['price'] - sorted_r[0]['price']}
    except:
        pass

    return render(request, 'comparison_chart.html', {
        'all_districts': all_districts, 'selected_districts': selected_districts,
        'chart_data': chart_data, 'summary_stats': summary_stats, 'arbitrage': arbitrage,
        'commodity': commodity, 'start_year': s_year, 'end_year': e_year
    })