from seleniumbase import Driver
import re

def clean_price(text):
    if not text: return None
    nums = re.findall(r'\d+', text.replace(',', ''))
    return int(nums[0]) if nums else None

def get_medicine_prices(medicine):
    # Initialize Driver in UC mode
    driver = Driver(uc=True, headless=True) # headless=True hides the browser window
    
    links = {
        "Apollo": f"https://www.apollopharmacy.in/search-medicines/{medicine}",
        "PharmEasy": f"https://pharmeasy.in/search/all?name={medicine}",
        "NetMeds": f"https://www.netmeds.com/products?q={medicine}"
    }

    results = []
    
    for site, url in links.items():
        try:
            driver.get(url)
            driver.sleep(7) # SeleniumBase built-in sleep
            
            if site == "Apollo":
                price_text = driver.get_text("div[class*='aV_']")
            elif site == "PharmEasy":
                price_text = driver.get_text("div[class*='ProductCard_ourPrice']")
            elif site == "NetMeds":
                price_text = driver.get_text("span.priceDisplay")
                
            final_price = clean_price(price_text)
        except Exception:
            final_price = "Not Found"

        results.append({
            "pharmacy": site,
            "price": final_price,
            "link": url
        })

    driver.quit()
    return results