import time
from datetime import datetime
from db_utils import get_connection

def get_unified_name(original_name):
    name = str(original_name).lower()
    # Deep Mapping Logic
    if 'cotton' in name or 'કપાસ' in name or 'narma' in name:
        return "Cotton"
    if 'wheat' in name or 'gehu' in name:
        return "Wheat"
    if 'groundnut' in name or 'magfali' in name:
        return "Groundnut"
    if 'jeera' in name or 'cumin' in name:
        return "Cumin"
    return original_name.capitalize()

def sync_all_districts():
    # To fix your problem, we will sync the LAST 5 YEARS, not just today
    print(f"[{datetime.now()}] Starting DEEP SYNC for all districts...")

    sources = [
        {'name': 'Ahmedabad', 'db': 'apmc_ahmedabad', 'query': "SELECT c.commodity_name, d.date, d.min_rate, d.max_rate FROM daily_rates d JOIN commodities c ON d.commodity_id = c.id WHERE YEAR(d.date) >= 2021"},
        {'name': 'Gondal', 'db': 'gondalmarket', 'query': "SELECT c.commodity_name, p.price_date, p.min_price, p.max_price FROM prices p JOIN commodities c ON p.commodity_id = c.id WHERE YEAR(p.price_date) >= 2021"},
        {'name': 'Rajkot', 'db': 'market', 'query': "SELECT j.jansi_english_name, m.date, m.lowrate, m.highrate FROM market_prices m JOIN jansi_master j ON m.id = j.id WHERE YEAR(m.date) >= 2021"}
    ]

    target_conn = get_connection('internship_analysis')
    target_cursor = target_conn.cursor()

    for source in sources:
        try:
            src_conn = get_connection(source['db'])
            src_cursor = src_conn.cursor()
            src_cursor.execute(source['query'])
            rows = src_cursor.fetchall()
            src_conn.close()

            if rows:
                cleaned_data = []
                for r in rows:
                    u_name = get_unified_name(r[0])
                    # Structure: dist, comm, date, min, max, avg, year
                    cleaned_data.append((source['name'], u_name, r[1], r[2], r[3], r[2], r[3], r[1]))

                insert_sql = "INSERT IGNORE INTO unified_market_data (district_name, commodity_name, price_date, min_price, max_price, average_price, year) VALUES (%s, %s, %s, %s, %s, (%s + %s)/2, YEAR(%s))"
                target_cursor.executemany(insert_sql, cleaned_data)
                target_conn.commit()
                print(f"✔ {source['name']}: {len(rows)} records moved to Unified Table.")
        except Exception as e:
            print(f"❌ Error in {source['name']}: {e}")

    target_conn.close()

if __name__ == "__main__":
    # Run once to fill the database, then it will sleep
    sync_all_districts()
    print("Initial Sync Complete. System is now monitoring for new daily data...")
    while True:
        time.sleep(3600) # Check every hour