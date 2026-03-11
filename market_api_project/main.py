from fastapi import FastAPI, Query, HTTPException
from db_utils import get_connection
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

# STEP 1: Initialize the App ONCE with your title
app = FastAPI(title="AgriLens Enterprise API")

# STEP 2: Configure CORS (Crucial for the UI Suggestions to work)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINT 1: REAL-TIME DATA ---
@app.get("/api/today/{district}", tags=["Real-Time Data"])
def get_daily_update(district: str):
    try:
        conn = get_connection('internship_analysis')
        cursor = conn.cursor(dictionary=True) 
        query = "SELECT * FROM unified_market_data WHERE district_name = %s AND price_date = CURDATE()"
        cursor.execute(query, (district,))
        results = cursor.fetchall()
        conn.close()
        return {"district": district, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 2: INTELLIGENT SEARCH (For Graphs) ---
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

        # Uses the bridge table to map "Cotton" to "Cotton B.T.", "Kapas", etc.
        query = """
            SELECT * FROM unified_market_data 
            WHERE commodity_name IN (
                SELECT raw_name FROM commodity_mapping WHERE standard_name = %s
            )
            AND year >= %s AND year <= %s
        """
        params = [commodity, start_year, end_year]

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

        return {"data": results}

    except Exception as e:
        print(f"SQL Error in Search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 3: DYNAMIC SUGGESTIONS (For UI Dropdown) ---
@app.get("/api/suggestions/", tags=["UI Helpers"])
def get_commodity_suggestions(district: Optional[List[str]] = Query(None)):
    try:
        conn = get_connection('internship_analysis')
        cursor = conn.cursor(dictionary=True)

        # Joins bridge table with real data to only suggest what is in stock
        query = """
            SELECT DISTINCT m.standard_name 
            FROM commodity_mapping m
            JOIN unified_market_data u ON m.raw_name = u.commodity_name
        """
        params = []

        if district:
            placeholders = ', '.join(['%s'] * len(district))
            query += f" WHERE u.district_name IN ({placeholders})"
            params.extend(district)

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        # Return clean list of strings: ["Cotton", "Wheat", etc.]
        return [row['standard_name'] for row in results]
    except Exception as e:
        print(f"SQL Error in Suggestions: {e}")
        return []