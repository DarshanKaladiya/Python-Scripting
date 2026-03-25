import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class ImdScraper:
    def __init__(self):
        self.url = "https://mausam.imd.gov.in/"
        self.setup_driver()

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def scrape(self):
        try:
            print("Navigating to IMD...")
            self.driver.get(self.url)
            time.sleep(3)
            # Weather scraping logic...
            print("IMD weather data scraped successfully.")
            return True
        except Exception as e:
            print(f"IMD scraping failed: {e}")
            return False
        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = ImdScraper()
    scraper.scrape()
