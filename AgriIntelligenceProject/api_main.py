from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from db_utils import get_connection
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware
from core.services.government_api import GovernmentAPIClient
from datetime import datetime

app = FastAPI(title="AgriIntelligence API", description="API for Agricultural Intelligence Engine")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to AgriIntelligence API"}

@app.get("/api/crops", tags=["Crops"])
def get_crops():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM master_crops")
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products", tags=["Products"])
def get_products(category: Optional[str] = None, brand: Optional[str] = None):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT p.*, c.name as brand_name FROM input_products p LEFT JOIN companies c ON p.brand_id = c.id WHERE 1=1"
        params = []
        if category:
            query += " AND p.category = %s"
            params.append(category)
        if brand:
            query += " AND c.name = %s"
            params.append(brand)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mandi/{crop_id}", tags=["Mandi"])
def get_mandi_prices(crop_id: int, state: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT crop_name FROM master_crops WHERE id = %s", (crop_id,))
        crop_row = cursor.fetchone()
        conn.close()
        
        if not crop_row:
            return []
            
        crop_name = crop_row["crop_name"]
        
        # Call government API directly
        api_client = GovernmentAPIClient()
        data = api_client.get_data("commodity_price", limit=50, commodity_filter=crop_name)
        
        results = []
        if data and "records" in data:
            for r in data["records"]:
                r_state = r.get("state") or r.get("State") or ""
                r_mandi = r.get("market") or r.get("Market") or ""
                r_mod = r.get("modal_price") or r.get("Modal_Price") or 0
                r_date_raw = r.get("arrival_date") or r.get("Arrival_Date") or ""
                
                try:
                    p_date = datetime.strptime(r_date_raw.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    p_date = datetime.now().strftime("%Y-%m-%d")
                
                if state and (state.strip().lower() != r_state.strip().lower()):
                    continue
                if start_date and p_date < start_date:
                    continue
                if end_date and p_date > end_date:
                    continue
                    
                results.append({
                    "id": len(results) + 1,
                    "crop_id": crop_id,
                    "state": r_state,
                    "mandi_name": r_mandi,
                    "modal_price": float(r_mod),
                    "price_date": p_date
                })
                
        # Sort by date desc
        results.sort(key=lambda x: x["price_date"], reverse=True)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crops/{crop_id}", tags=["Crops"])
def get_crop_detail(crop_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM master_crops WHERE id = %s", (crop_id,))
        result = cursor.fetchone()
        conn.close()
        if not result:
            raise HTTPException(status_code=404, detail="Crop not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/advisories/{crop_id}", tags=["Intelligence"])
def get_crop_advisories(crop_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crop_advisories WHERE crop_id = %s", (crop_id,))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-pulse", tags=["Intelligence"])
def get_market_pulse():
    try:
        api_client = GovernmentAPIClient()
        data = api_client.get_data("market_price", limit=50)
        
        if not data or "records" not in data:
            return {"gainers": [], "losers": []}
            
        records = data["records"]
        pulse_data = []
        for r in records:
            try:
                mod_price = float(r.get("modal_price") or r.get("Modal_Price") or 0)
                pulse_data.append({
                    "id": len(pulse_data) + 1,
                    "crop_name": r.get("commodity") or r.get("Commodity") or "",
                    "category": "Market",
                    "current_price": mod_price,
                    "previous_price": mod_price * 0.98, # Mocking previous price for direct API setup
                    "pct_change": 2.0 # Mocking positive change
                })
            except:
                pass
                
        pulse_data.sort(key=lambda x: x["current_price"], reverse=True)
        seen = set()
        unique_pulse = []
        for p in pulse_data:
            if p["crop_name"] and p["crop_name"] not in seen:
                seen.add(p["crop_name"])
                unique_pulse.append(p)
                
        gainers = unique_pulse[:5]
        losers = unique_pulse[-5:] if len(unique_pulse) > 10 else []
        
        # Make losers actually negative
        for l in losers:
            l["pct_change"] = -1.5
            l["previous_price"] = l["current_price"] * 1.015
            
        return {"gainers": gainers, "losers": losers}
    except Exception as e:
        return {"gainers": [], "losers": []}

@app.get("/api/companies", tags=["Directory"])
def get_companies():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM companies")
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compare", tags=["Intelligence"])
def compare_products(technical_name: str):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        # Intelligence Logic: Compare products with same technical name and rank by price per unit
        query = """
        SELECT p.*, c.name as brand_name 
        FROM input_products p 
        LEFT JOIN companies c ON p.brand_id = c.id 
        WHERE p.technical_name = %s 
        ORDER BY (p.price / p.unit_value) ASC
        """
        cursor.execute(query, (technical_name,))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
