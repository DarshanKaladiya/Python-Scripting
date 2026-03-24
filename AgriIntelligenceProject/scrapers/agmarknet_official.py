import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from db_utils import get_connection

class AgmarknetScraper:
    def __init__(self):
        self.url = "https://agmarknet.gov.in/"
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.driver, 30)

    def scrape_homepage_mandi(self):
        """Scrape the 'Market Wise Price & Arrival' section on homepage"""
        print(f"Accessing Agmarknet: {self.url}...")
        self.driver.get(self.url)
        time.sleep(5)
        
        # Locate the results table on homepage (usually in overflow-x-auto)
        try:
            # We might need to select a state to trigger the table if it's empty
            # But usually it shows 'Recent'
            table = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.overflow-x-auto table")))
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"Found {len(rows)} recent government records on homepage.")
            
            records = []
            for row in rows[1:]: # Skip header
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 5:
                    records.append({
                        "group": cols[0].text.strip(),
                        "commodity": cols[1].text.strip(),
                        "msp": cols[2].text.strip(),
                        "price_data": cols[3].text.strip(), # This contains 3 days of prices
                        "arrival_data": cols[4].text.strip()
                    })
            return records
        except Exception as e:
            print(f"Homepage scrape failed: {e}")
            return []

    def save_to_db(self, records):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get crop mapping
        cursor.execute("SELECT id, crop_name FROM master_crops")
        crop_map = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        count = 0
        for r in records:
            commodity = r["commodity"].lower()
            crop_id = None
            for cname, cid in crop_map.items():
                if cname in commodity or commodity in cname:
                    crop_id = cid
                    break
            
            if not crop_id: continue
            
            # Note: Agmarknet homepage table price format is "Price1 | Price2 | Price3"
            # We'll take the most recent (usually the first or last depending on site update)
            prices = [p.strip() for p in r["price_data"].split("|") if p.strip().isdigit()]
            if not prices: continue
            
            modal_p = float(prices[0])
            
            try:
                sql = """INSERT INTO mandi_prices 
                         (crop_id, state, mandi_name, modal_price, price_date) 
                         VALUES (%s, %s, %s, %s, %s)
                         ON DUPLICATE KEY UPDATE modal_price=VALUES(modal_price)"""
                # Homepage doesn't always specify state per row in the 'Recent' view, might need state filter
                cursor.execute(sql, (crop_id, "National", "Agmarknet Central", modal_p, time.strftime("%Y-%m-%d")))
                count += 1
            except Exception as e:
                print(f"Insert error: {e}")
                
        conn.commit()
        print(f"Successfully integrated {count} official Agmarknet records.")
        cursor.close()
        conn.close()

    def run(self):
        try:
            data = self.scrape_homepage_mandi()
            self.save_to_db(data)
        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = AgmarknetScraper()
    scraper.run()
