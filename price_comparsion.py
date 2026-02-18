from seleniumbase import Driver
import pandas as pd
import time
import re

# Logic to clean price text like "₹150.00" or "150" into a number
def clean_price(text):
    if not text: return None
    nums = re.findall(r'\d+', text.replace(',', ''))
    return int(nums[0]) if nums else None

# Initialize Driver in Undetectable (UC) mode to bypass bot-checks
driver = Driver(uc=True)

medicine = input("Enter medicine name: ")

#Search Links
links = {
    "Apollo": f"https://www.apollopharmacy.in/search-medicines/{medicine}",
    "PharmEasy": f"https://pharmeasy.in/search/all?name={medicine}",
    "NetMeds": f"https://www.netmeds.com/products?q={medicine}"
}

results = []
print(f"\nStarting price comparison for: {medicine}...")

for site, url in links.items():
    print(f"Searching {site}...")
    try:
        driver.get(url)
        time.sleep(7) # Wait for prices to load dynamically
        
        # Site-specific selectors
        if site == "Apollo":
            # Finding the present-price container
            price_text = driver.get_text("div[class*='aV_']")
        elif site == "PharmEasy":
            # Finding the PharmEasy price div
            price_text = driver.get_text("div[class*='ProductCard_ourPrice']")
        elif site == "NetMeds":
            price_text = driver.get_text("span.priceDisplay")
            
        final_price = clean_price(price_text)
    except Exception:
        final_price = None # Mark as None if not found

    results.append({
        "Medicine": medicine.upper(),
        "Pharmacy": site,
        "Price": final_price,
        "Link": url
    })

driver.quit()

df = pd.DataFrame(results)

df["Cheapest Price"] = df["Price"].min()

output_file = f"{medicine.replace(' ', '_')}_Final_Report.csv"
df.to_csv(output_file, index=False)

print(f"\nAll 3 prices checked! File saved: {output_file}")