import time
import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from db_utils import get_connection

class AgriProductScraper:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        
        # Chrome Setup
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--log-level=3")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def get_company_id(self, company_name):
        self.cursor.execute("SELECT id FROM companies WHERE name = %s", (company_name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            self.cursor.execute("INSERT INTO companies (name) VALUES (%s)", (company_name,))
            self.conn.commit()
            return self.cursor.lastrowid

    def normalize_unit(self, unit_str):
        unit_str = unit_str.lower().strip()
        # Look for patterns like 500 gm, 1 kg, 250 ml, 1 L
        match = re.search(r'(\d+\.?\d*)\s*(kg|gm|g|ml|l|ltr|liter)', unit_str)
        if match:
            value = float(match.group(1))
            measure = match.group(2)
            if measure in ['gm', 'g']:
                return value, 'gm'
            if measure in ['kg']:
                return value, 'kg'
            if measure in ['ml']:
                return value, 'ml'
            if measure in ['l', 'ltr', 'liter']:
                return value, 'L'
        return 1.0, 'unit'

    def scrape_agribegri(self, category_url, category_name, max_load_clicks=5):
        print(f"\n>>> Scraping Category: {category_name} from {category_url}")
        self.driver.get(category_url)
        
        # 1. Handle "Load More" to get more products
        for i in range(max_load_clicks):
            try:
                # Wait for potential Load More button
                print(f"Attempting Load More #{i+1}...")
                load_more = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load More')]"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", load_more)
                time.sleep(1)
                load_more.click()
                time.sleep(3) # Wait for AJAX load
            except Exception:
                print("No more 'Load More' button found or timeout.")
                break

        # 2. Extract Product Cards
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'article[aria-label="Product Card"]'))
            )
            products = self.driver.find_elements(By.CSS_SELECTOR, 'article[aria-label="Product Card"]')
            print(f"Total products found after loading: {len(products)}")

            for prod in products:
                try:
                    name = prod.find_element(By.CSS_SELECTOR, 'h3').text.strip()
                    # Price handling
                    try:
                        price_text = prod.find_element(By.CSS_SELECTOR, 'section section span:nth-of-type(1)').text
                        price = float(price_text.replace('₹', '').replace(',', '').strip())
                    except:
                        price = 0.0

                    # Brand handling
                    try:
                        brand_name = prod.find_element(By.CSS_SELECTOR, 'section > span:first-child').text.strip()
                    except:
                        brand_name = "Generic"
                    brand_id = self.get_company_id(brand_name)

                    # Unit handling
                    try:
                        unit_str = prod.find_element(By.CSS_SELECTOR, 'section section span:nth-of-type(3)').text.strip()
                    except:
                        unit_str = "1 Unit"
                    unit_val, unit_measure = self.normalize_unit(unit_str)

                    image_url = prod.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')

                    technical_name = "Generic"
                    tech_match = re.search(r'\((.*?)\)', name)
                    if tech_match:
                        technical_name = tech_match.group(1)

                    sql = """
                    INSERT INTO input_products 
                    (category, product_name, brand_id, technical_name, price, unit_value, unit_measure, source_url, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE price = VALUES(price), last_updated = CURRENT_TIMESTAMP
                    """
                    self.cursor.execute(sql, (category_name, name, brand_id, technical_name, price, unit_val, unit_measure, category_url, image_url))
                    self.conn.commit()
                except Exception as e:
                    continue # Skip problematic products
            
            print(f"Category {category_name} processed.")
        except Exception as e:
            print(f"Error loading products for {category_name}: {e}")

    def close(self):
        self.driver.quit()
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    scraper = AgriProductScraper()
    # Comprehensive category mapping
    categories = [
        ('https://agribegri.com/seeds/', 'Seed'),
        ('https://agribegri.com/fertilizers/bio-fertilizers', 'Fertilizer'), # Subset of fertilizers
        ('https://agribegri.com/fertilizers/water-soulable-fertilizers', 'Fertilizer'),
        ('https://agribegri.com/crop-protection/insecticides', 'Pesticide'),
        ('https://agribegri.com/crop-protection/herbicides', 'Herbicide'),
        ('https://agribegri.com/crop-protection/fungicides', 'Fungicide')
    ]
    
    for url, cat in categories:
        scraper.scrape_agribegri(url, cat, max_load_clicks=3) # Limit to 3 clicks per category for speed
    
    scraper.close()
