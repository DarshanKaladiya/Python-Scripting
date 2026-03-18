import wikipedia
import re
from db_utils import get_connection

def scrape_master_crops():
    print("Fetching LIVE biological facts from Wikipedia...")
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT crop_name FROM master_crops")
    records = cursor.fetchall()
    crops = [r[0] for r in records]
    
    for crop in crops:
        try:
            # Fetch summary and scientific name from Wikipedia
            page = wikipedia.page(f"{crop} agriculture")
            summary = wikipedia.summary(f"{crop} agriculture", sentences=2)
            
            # Simple scientific name extraction heuristic
            scientific_name = "Unknown"
            match = re.search(r'\(([A-Z][a-z]+ [a-z]+)\)', summary)
            if match:
                scientific_name = match.group(1)
            
            sql = """INSERT INTO master_crops 
                     (crop_name, scientific_name, description) 
                     VALUES (%s, %s, %s)
                     ON DUPLICATE KEY UPDATE description=VALUES(description)"""
            cursor.execute(sql, (crop, scientific_name, summary[:1000]))
            print(f"Scraped structural data for: {crop}")
        except Exception as e:
            print(f"Failed to fetch live data for {crop}: {e}")
            
    conn.commit()
    cursor.close()
    conn.close()
    print("Biological facts real-time synchronization complete.")

if __name__ == "__main__":
    scrape_master_crops()
