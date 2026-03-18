from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from db_utils import get_connection
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware

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
        query = "SELECT * FROM mandi_prices WHERE crop_id = %s"
        params = [crop_id]
        if state:
            query += " AND state = %s"
            params.append(state)
        if start_date:
            query += " AND price_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND price_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY price_date DESC"
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
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
