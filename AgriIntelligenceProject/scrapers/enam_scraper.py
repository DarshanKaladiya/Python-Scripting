import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from db_utils import get_connection

class ENAMScraper:
    def __init__(self):
        self.url = "https://enam.gov.in/web/dashboard/trade-data"
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument('--ignore-certificate-errors')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.driver, 30)

    def login_and_navigate(self):
        print(f"Opening e-NAM Trade Data: {self.url}...")
        self.driver.get(self.url)
        time.sleep(5)
        
        try:
            # Handle the 'Attention' modal
            close_btn = self.driver.find_element(By.CSS_SELECTOR, "a.close")
            if close_btn.is_displayed():
                close_btn.click()
                print("Modal dismissed.")
        except:
            pass

    def clean_text(self, text):
        return re.sub(r'\(.*?\)', '', text).replace('/', '').strip().lower()

    def scrape_data(self):
        self.login_and_navigate()
        
        # Select 'All' in State if possible, or iterate common states
        # For this demo/batch, we click refresh on the default (often empty until refresh)
        try:
            refresh_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "refresh")))
            self.driver.execute_script("arguments[0].click();", refresh_btn)
            print("Refreshing data...")
            time.sleep(10) # Wait for table population
        except Exception as e:
            print(f"Refresh failed: {e}")

        rows = self.driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
        print(f"Scanning {len(rows)} potential rows...")
        
        results = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 10:
                results.append({
                    "state": cols[0].text.strip(),
                    "apmc": cols[1].text.strip(),
                    "commodity": cols[2].text.strip(),
                    "min_price": cols[3].text.strip(),
                    "modal_price": cols[4].text.strip(),
                    "max_price": cols[5].text.strip(),
                    "unit": cols[8].text.strip(),
                    "date": cols[9].text.strip()
                })
        return results

    def save_records(self, records):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get category-aware crop mapping
        cursor.execute("SELECT id, crop_name, category FROM master_crops")
        crops_db = cursor.fetchall()
        
        count = 0
        for r in records:
            # Fuzzy match: "Arhar Whole / Tur (Red Gram)" -> "Redgram (Tur)"
            comm_clean = self.clean_text(r["commodity"])
            crop_id = None
            
            for cid, cname, cat in crops_db:
                cn_clean = self.clean_text(cname)
                # Check if important keywords match
                if cn_clean in comm_clean or comm_clean in cn_clean:
                    crop_id = cid
                    break
            
            if not crop_id: continue
            
            try:
                # Cleanup prices
                try:
                    p_min = float(r["min_price"].replace(",", ""))
                    p_max = float(r["max_price"].replace(",", ""))
                    p_mod = float(r["modal_price"].replace(",", ""))
                except:
                    continue
                
                # Date format
                try:
                    d_obj = time.strptime(r["date"], "%d-%m-%Y")
                    db_date = time.strftime("%Y-%m-%d", d_obj)
                except:
                    db_date = time.strftime("%Y-%m-%d")

                sql = """INSERT INTO mandi_prices 
                         (crop_id, state, mandi_name, min_price, max_price, modal_price, units, price_date) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                         ON DUPLICATE KEY UPDATE modal_price=VALUES(modal_price)"""
                cursor.execute(sql, (crop_id, r["state"], r["apmc"], p_min, p_max, p_mod, r["unit"], db_date))
                count += 1
            except Exception as e:
                print(f"Insert error: {e}")
        
        conn.commit()
        print(f"Successfully integrated {count} official e-NAM records into categorized database.")
        cursor.close()
        conn.close()

if __name__ == "__main__":
    scraper = ENAMScraper()
    try:
        data = scraper.scrape_data()
        scraper.save_records(data)
    finally:
        scraper.driver.quit()
