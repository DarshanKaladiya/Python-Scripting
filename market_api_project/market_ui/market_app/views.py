from django.shortcuts import render
import requests

def comparison_chart_view(request):
    # 1. Capture filters from the Sidebar
    search_term = request.GET.get('commodity', 'Cotton')
    selected_districts = request.GET.getlist('districts')
    start_year = request.GET.get('start_year', 2021)
    end_year = request.GET.get('end_year', 2026)

    if not selected_districts:
        selected_districts = ['Ahmedabad', 'Gondal', 'Rajkot']

    # 2. Fetch data directly from your working FastAPI
    API_URL = "http://127.0.0.1:8000/api/search/"
    params = {
        'commodity': search_term,
        'start_year': start_year,
        'end_year': end_year,
        'district': selected_districts
    }

    chart_data = {}
    summary_stats = []
    api_error = None

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        if response.status_code == 200:
            # Your API returns {"data": [...]}
            api_response = response.json()
            api_data = api_response.get('data', [])

            # 3. Group the data by District for the Graph
            for dist in selected_districts:
                # Filter rows for this specific district
                d_rows = [r for r in api_data if r.get('district_name') == dist]
                
                if d_rows:
                    # Sort by date for a smooth chart line
                    d_rows.sort(key=lambda x: x['price_date'])
                    
                    chart_data[dist] = [
                        {'price_date': str(r['price_date']), 'average_price': float(r['average_price'])} 
                        for r in d_rows
                    ]

                    # Calculations for the Table
                    prices = [float(r['average_price']) for r in d_rows]
                    summary_stats.append({
                        'district': dist,
                        'avg': round(sum(prices)/len(prices), 2),
                        'max': max(prices),
                        'last': prices[-1],
                        'trend': "UP" if len(prices) > 1 and prices[-1] > prices[-2] else "DOWN"
                    })
        else:
            api_error = f"API returned error: {response.status_code}"
    except Exception as e:
        api_error = f"Could not connect to API: {str(e)}"

    return render(request, 'comparison_chart.html', {
        'chart_data': chart_data,
        'summary_stats': summary_stats,
        'commodity': search_term,
        'selected_districts': selected_districts,
        'all_districts': ['Ahmedabad', 'Gondal', 'Rajkot'],
        'api_error': api_error,
        'start_year': start_year,
        'end_year': end_year
    })