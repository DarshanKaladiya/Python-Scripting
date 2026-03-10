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

# Advanced Multi-District Search
@app.get("/api/search/", tags=["Market Analysis"])
def filter_market_data(
    commodity: str = Query(..., example="Cotton"),
    start_year: int = Query(2021),
    end_year: int = Query(2026),
    district: Optional[List[str]] = Query(None)
):
    try:
        conn = get_connection('internship_analysis')
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM unified_market_data WHERE commodity_name LIKE %s AND year >= %s AND year <= %s"
        params = [f"%{commodity}%", start_year, end_year]

        if district:
            placeholders = ', '.join(['%s'] * len(district))
            query += f" AND district_name IN ({placeholders})"
            params.extend(district)

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        conn.close()
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))