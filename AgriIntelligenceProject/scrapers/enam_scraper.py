import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

class EnamScraper:
    def __init__(self):
        self.url = "https://www.enam.gov.in/web/dashboard/mandi-price"
        self.setup_driver()

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def scrape(self):
        try:
            print("Navigating to e-NAM...")
            self.driver.get(self.url)
            time.sleep(5)
            # Scrape logic...
            print("e-NAM data scraped successfully.")
            return True
        except Exception as e:
            print(f"e-NAM scraping failed: {e}")
            return False
        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = EnamScraper()
    scraper.scrape()
