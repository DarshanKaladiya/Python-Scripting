import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from db_utils import get_connection
import time
import io
from datetime import datetime

class IndianMandiScraper:
    def __init__(self):
        print("Initializing Indian Marketing Yard Scraper...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def scrape_daily_bulletin(self):
        url = "https://vegetablemarketprice.com/market/maharashtra/today"
        print(f"Connecting to Indian market portal: {url}...")
        self.driver.get(url)
        time.sleep(3) 
        
        try:
            tables = pd.read_html(io.StringIO(self.driver.page_source))
            print(f"Found {len(tables)} data table(s) on the portal.")
            
            inserted_count = 0
            for df in tables:
                df.columns = [str(c).lower() for c in df.columns]
                
                for index, row in df.iterrows():
                    commodity = None
                    min_p = 0.0
                    max_p = 0.0
                    modal_p = 0.0
                    
                    # Positional heuristics for this specific Indian marketing yard layout
                    if len(df.columns) >= 6:
                        commodity = str(row.iloc[1]).split('(')[0].strip() # 2nd column often the name
                        
                        price_val = str(row.iloc[2]).replace('₹', '').strip() # Wholesale
                        if '-' in price_val:
                            parts = price_val.split('-')
                            min_p = float(parts[0].strip())
                            max_p = float(parts[1].strip())
                            modal_p = (min_p + max_p) / 2
                        elif price_val.replace('.','',1).isdigit():
                            modal_p = float(price_val)
                            min_p = modal_p * 0.95
                            max_p = modal_p * 1.05
                            
                        # Retail
                        retail_val = str(row.iloc[3]).replace('₹', '').strip()
                        retail_min_p, retail_max_p = 0.0, 0.0
                        if '-' in retail_val:
                            parts = retail_val.split('-')
                            retail_min_p = float(parts[0].strip())
                            retail_max_p = float(parts[1].strip())
                        elif retail_val.replace('.','',1).isdigit():
                            retail_min_p = float(retail_val)
                            retail_max_p = float(retail_val)
                            
                        # Shopping Mall
                        mall_val = str(row.iloc[4]).replace('₹', '').strip()
                        mall_min_p, mall_max_p = 0.0, 0.0
                        if '-' in mall_val:
                            parts = mall_val.split('-')
                            mall_min_p = float(parts[0].strip())
                            mall_max_p = float(parts[1].strip())
                        elif mall_val.replace('.','',1).isdigit():
                            mall_min_p = float(mall_val)
                            mall_max_p = float(mall_val)
                            
                        # Units
                        units_val = str(row.iloc[5]).strip()
                            
                    if commodity and commodity.lower() != 'nan' and modal_p > 0:
                        # Match existing crops to prevent spamming master_crops with random commodities
                        search_term = commodity.split()[0]
                        self.cursor.execute("SELECT id FROM master_crops WHERE crop_name LIKE %s LIMIT 1", (f"%{search_term}%",))
                        res = self.cursor.fetchone()
                        if res:
                            crop_id = res[0]
                            date_str = datetime.now().strftime('%Y-%m-%d')
                            sql = """INSERT INTO mandi_prices 
                                     (crop_id, state, district, mandi_name, price_date, min_price, max_price, modal_price, retail_min_price, retail_max_price, mall_min_price, mall_max_price, units)
                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                     ON DUPLICATE KEY UPDATE modal_price=VALUES(modal_price), retail_max_price=VALUES(retail_max_price), mall_max_price=VALUES(mall_max_price)"""
                            self.cursor.execute(sql, (crop_id, "Maharashtra", "Local District", "Indian Marketing Yard", date_str, round(min_p, 2), round(max_p, 2), round(modal_p, 2), round(retail_min_p, 2), round(retail_max_p, 2), round(mall_min_p, 2), round(mall_max_p, 2), units_val))
                            inserted_count += 1
            
            self.conn.commit()
            print(f"Successfully scraped and inserted {inserted_count} real Mandi prices from the Indian Marketing Yard Website.")
            
        except Exception as e:
            print("Failed to parse tables: ", e)
        finally:
            self.driver.quit()
            self.cursor.close()
            self.conn.close()

if __name__ == "__main__":
    scraper = IndianMandiScraper()
    scraper.scrape_daily_bulletin()
