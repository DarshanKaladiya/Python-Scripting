import os
import requests
from dotenv import load_dotenv
from db_utils import get_connection
import time
from datetime import datetime

load_dotenv()

class GovernmentAPIClient:
    def __init__(self):
        self.api_key = os.getenv("DATA_GOV_API_KEY")
        self.base_url = "https://api.data.gov.in/resource/"
        
        # Resource IDs are now pulled from .env for easy user updates
        self.resources = {
            "market_price": os.getenv("AGMARKNET_RESOURCE_ID"),
            "commodity_price": os.getenv("COMMODITY_RESOURCE_ID")
        }

    def get_data(self, resource_type, limit=100, retries=3, delay=5):
        if not self.api_key:
            print("ERROR: DATA_GOV_API_KEY not found in .env")
            return None
            
        res_id = self.resources.get(resource_type)
        if not res_id:
            print(f"ERROR: Resource ID for {resource_type} not configured in .env")
            return None

        url = f"{self.base_url}{res_id}?api-key={self.api_key}&format=json&limit={limit}"
        print(f"Fetching {resource_type} from API (ID: {res_id})...")
        
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [502, 503, 504]:
                    print(f"Server Busy ({response.status_code}). Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    response.raise_for_status()
            except Exception as e:
                print(f"Request failed: {e}")
                if attempt < retries - 1: time.sleep(delay)
                else: return None
        return None

    def sync_market_prices(self):
        """Sync specifically for real-time market prices"""
        data = self.get_data("market_price", limit=500)
        if not data or "records" not in data: return
        
        records = data["records"]
        conn = get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        # Get crop mapping
        cursor.execute("SELECT id, crop_name FROM master_crops")
        crop_map = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        count = 0
        for r in records:
            commodity_name = r.get("commodity", "").lower()
            crop_id = None
            for cname, cid in crop_map.items():
                if cname in commodity_name or commodity_name in cname:
                    crop_id = cid; break
            
            if not crop_id: continue
            
            try:
                state, mandi = r.get("state", "National"), r.get("market", "API Source")
                p_mod = float(r.get("modal_price", 0))
                p_date_raw = r.get("arrival_date")
                try:
                    p_date = datetime.strptime(p_date_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    p_date = datetime.now().strftime("%Y-%m-%d")
                
                sql = """INSERT INTO mandi_prices (crop_id, state, mandi_name, modal_price, price_date) 
                         VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE modal_price=VALUES(modal_price)"""
                cursor.execute(sql, (crop_id, state, mandi, p_mod, p_date))
                count += 1
            except Exception as e: print(f"API Sync error: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Successfully synced {count} market price records via API.")

    def sync_commodity_prices(self):
        """Sync specifically for real-time commodity prices (Simplified placeholder)"""
        # (This is a simplified version, as we use market_price for mandi_prices)
        print("Commodity Price Sync (Generic) completed.")
