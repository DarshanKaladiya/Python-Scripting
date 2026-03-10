from fastapi import FastAPI, Query, HTTPException
from db_utils import get_connection
from typing import List, Optional

app = FastAPI(title="AgriLens Enterprise API")

# RESTORED: Daily Price Option
@app.get("/api/today/{district}", tags=["Real-Time Data"])
def get_daily_update(district: str):
    try:
        conn = get_connection('internship_analysis')
        cursor = conn.cursor(dictionary=True) 
        # Fetches only the latest record for today
        query = "SELECT * FROM unified_market_data WHERE district_name = %s AND price_date = CURDATE()"
        cursor.execute(query, (district,))
        results = cursor.fetchall()
        conn.close()
        return {"district": district, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Updated main.py with Intelligent Multilingual Search
# main.py (FastAPI)

@app.get("/api/search/")
def filter_market_data(
    commodity: str = Query(..., example="Cotton"),
    start_year: int = Query(2021),
    end_year: int = Query(2026),
    district: Optional[List[str]] = Query(None)
):
    try:
        conn = get_connection('internship_analysis')
        cursor = conn.cursor(dictionary=True)

        # WRITE THE QUERY HERE:
        # This subquery finds all 'raw_names' from your mapping table 
        # that match the user's search term.
        query = """
            SELECT * FROM unified_market_data 
            WHERE commodity_name IN (
                SELECT raw_name FROM commodity_mapping WHERE standard_name = %s
            )
            AND year >= %s AND year <= %s
        """
        params = [commodity, start_year, end_year]

        # Add the district filter to the query if the user selected any
        if district:
            placeholders = ', '.join(['%s'] * len(district))
            query += f" AND district_name IN ({placeholders})"
            params.extend(district)

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        # Format dates for JSON safety
        for row in results:
            row['price_date'] = str(row['price_date'])

        # Return the data to Django
        return {"data": results}

    except Exception as e:
        print(f"SQL Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))