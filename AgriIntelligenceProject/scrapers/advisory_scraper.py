import feedparser
from db_utils import get_connection

def scrape_live_advisories():
    print("Fetching LIVE Agromet Weather and Pest Advisories via Google News RSS...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Standardize our master crop associations
    cursor.execute("SELECT id, crop_name FROM master_crops LIMIT 1")
    master_id = cursor.fetchone()
    if not master_id:
        print("Master crops must be seeded first!")
        return
        
    # Fetch latest generic Indian agricultural advisories News RSS
    feed_url = "https://news.google.com/rss/search?q=India+agriculture+weather+pest+advisory&hl=en-IN&gl=IN&ceid=IN:en"
    parsed = feedparser.parse(feed_url)
    
    advisories = []
    for entry in parsed.entries[:10]: # Top 10 most recent live advisories
        title = entry.title
        link = entry.link
        # Categorize
        req_type = "Fertilizer"
        if "pest" in title.lower() or "disease" in title.lower(): req_type = "Pesticide"
        if "seed" in title.lower() or "sowing" in title.lower(): req_type = "Seed"
        
        advisories.append((master_id[0], "Current Conditions", req_type, title, "Real-time Update", link[:1000]))
        
    if advisories:
        cursor.execute("DELETE FROM crop_advisories WHERE growth_stage = 'Current Conditions'") # Clear out stale real-time advice only
        sql = "INSERT INTO crop_advisories (crop_id, growth_stage, requirement_type, technical_recommendation, dosage_per_acre, notes) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.executemany(sql, advisories)
        
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Scraped and injected {len(advisories)} LIVE farming advisories.")

if __name__ == "__main__":
    scrape_live_advisories()
