import yfinance as yf
from db_utils import get_connection

def scrape_real_companies():
    print("Fetching LIVE corporate intelligence from NSE (National Stock Exchange)...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Top publicly listed Indian Agrochemical & Fertilizer companies
    tickers = {
        "UPL.NS": "UPL",
        "PIIND.NS": "PI Industries",
        "BAYERCROP.NS": "Bayer CropScience",
        "COROMANDEL.NS": "Coromandel International",
        "CHAMBLFERT.NS": "Chambal Fertilisers",
        "BHARATRAS.NS": "Bharat Rasayan",
        "RALLIS.NS": "Rallis India",
        "DEEPAKFERT.NS": "Deepak Fertilisers"
    }
    
    for symbol, backup_name in tickers.items():
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Extract live factual data
            comp_name = info.get("longName", backup_name)
            website = info.get("website", f"https://www.google.com/search?q={backup_name}")
            
            sql = """INSERT INTO companies (name, website_url) 
                     VALUES (%s, %s)
                     ON DUPLICATE KEY UPDATE website_url = VALUES(website_url)"""
            cursor.execute(sql, (comp_name, website))
            print(f"Scraped structural data for: {comp_name}")
        except Exception as e:
            print(f"Failed to fetch live data for {symbol}: {e}")
            
    conn.commit()
    cursor.close()
    conn.close()
    print("Corporate real-time synchronization complete.")

if __name__ == "__main__":
    scrape_real_companies()
