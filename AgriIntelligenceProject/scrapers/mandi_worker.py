import requests
import json
from db_utils import get_connection
from datetime import datetime
import time

class IndianMandiScraper:
    def __init__(self):
        print("Initializing Indian Marketing Yard Scraper (API Version)...")
        self.conn = get_connection()
        self.cursor = self.conn.cursor(buffered=True)

    def scrape_daily_bulletin(self, date_str=None, state='maharashtra'):
        if not date_str or date_str == 'today':
            db_date = datetime.now().strftime('%Y-%m-%d')
        else:
            db_date = date_str

        url = f"https://vegetablemarketprice.com/api/dataapi/market/{state.lower().replace(' ', '')}/daywisedata?date={db_date}"
        print(f"Fetching Mandi data for {state} on {db_date} via API: {url}...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"API Error: {response.status_code}")
                return
                
            json_data = response.json()
            if 'data' not in json_data:
                print(f"No data for {state} on {db_date}.")
                return
                
            data_list = json_data['data']
            print(f"Retrieved {len(data_list)} entries.")
            
            inserted_count = 0
            for item in data_list:
                try:
                    # Priority: vegName, columnNameEng, vegettable
                    raw_name = item.get('vegName') or item.get('columnNameEng') or item.get('vegettable') or ''
                    commodity = raw_name.split('(')[0].strip()
                    
                    price_val = item.get('price')
                    if price_val is None: continue
                    wholesale_price = float(price_val)
                    
                    retail_range = item.get('retailPrice') or item.get('retailprice') or '0-0'
                    mall_range = item.get('shopingMallPrice') or item.get('shoppingMallPrice') or '0-0'
                    units_val = item.get('units', '1kg')
                    
                    if not commodity or wholesale_price <= 0:
                        continue
                        
                    # Parse Retail/Mall Ranges
                    def parse_range(price_range):
                        if not price_range: return 0.0, 0.0
                        # Handle potential numeric values instead of strings
                        if isinstance(price_range, (int, float)):
                            return float(price_range), float(price_range)
                        
                        ps = str(price_range).replace('₹', '').replace(',', '').strip()
                        if not ps or ps.lower() in ['0', '0-0', 'none', 'null', '']: return 0.0, 0.0
                        
                        if '-' in ps:
                            parts = ps.split('-')
                            try:
                                return float(parts[0].strip()), float(parts[1].strip())
                            except:
                                return 0.0, 0.0
                        else:
                            try:
                                val = float(ps)
                                return val, val
                            except:
                                return 0.0, 0.0

                    ret_min, ret_max = parse_range(retail_range)
                    mall_min, mall_max = parse_range(mall_range)
                    
                    min_p = wholesale_price * 0.95
                    max_p = wholesale_price * 1.05
                    modal_p = wholesale_price
                    
                    # Robust Crop Matching
                    def normalize(n):
                        return n.lower().replace('chilli', 'chili').strip()

                    norm_name = normalize(commodity)
                    import re
                    clean_name = re.sub(r'\(.*\)', '', norm_name).strip()
                    
                    search_terms = [clean_name]
                    if ' ' in clean_name:
                        search_terms.extend(clean_name.split())
                    
                    crop_id = None
                    for term in search_terms:
                        if not term or len(term) < 3: continue
                        self.cursor.execute("SELECT id FROM master_crops WHERE crop_name LIKE %s OR %s LIKE CONCAT('%', crop_name, '%')", (f"%{term}%", term))
                        res = self.cursor.fetchone()
                        if res:
                            crop_id = res[0]
                            break
                    
                    if crop_id:
                        sql = """INSERT INTO mandi_prices 
                                 (crop_id, state, district, mandi_name, price_date, min_price, max_price, modal_price, retail_min_price, retail_max_price, mall_min_price, mall_max_price, units)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                 ON DUPLICATE KEY UPDATE 
                                    modal_price=VALUES(modal_price), 
                                    min_price=VALUES(min_price),
                                    max_price=VALUES(max_price),
                                    retail_min_price=VALUES(retail_min_price),
                                    retail_max_price=VALUES(retail_max_price), 
                                    mall_min_price=VALUES(mall_min_price),
                                    mall_max_price=VALUES(mall_max_price),
                                    units=VALUES(units)"""
                        self.cursor.execute(sql, (crop_id, state.capitalize(), "General Market", f"{state.capitalize()} APMC", db_date, round(min_p, 2), round(max_p, 2), round(modal_p, 2), round(ret_min, 2), round(ret_max, 2), round(mall_min, 2), round(mall_max, 2), units_val))
                        inserted_count += 1
                        
                except Exception as e:
                    print(f"Insertion error for {commodity}: {e}")
                    continue
            
            self.conn.commit()
            print(f"[{state}] Processed {inserted_count} records for {db_date}.")
            
        except Exception as e:
            print(f"Error for {state} on {db_date}: {e}")
        finally:
            self.cursor.close()
            self.conn.close()

if __name__ == "__main__":
    import sys
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    scraper = IndianMandiScraper()
    scraper.scrape_daily_bulletin(target_date)
