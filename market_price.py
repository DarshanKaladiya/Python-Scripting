import mysql.connector
from datetime import datetime, timedelta

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
}

def get_data_from_db(db_name, query):
    """Helper function to connect, fetch, and close immediately."""
    try:
        conn = mysql.connector.connect(**db_config, database=db_name)
        # Use buffered=True to fetch all results at once and free the server
        cursor = conn.cursor(buffered=True)
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data
    except mysql.connector.Error as err:
        print(f"Error in {db_name}: {err}")
        return []

def migrate_data():
    five_years_ago = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
    
    # 1. Fetch Ahmedabad
    print("Fetching Ahmedabad...")
    q_ahmedabad = f"""
        SELECT 'Ahmedabad', c.commodity_name, d.date, d.min_rate, d.max_rate 
        FROM daily_rates d
        JOIN commodities c ON d.commodity_id = c.id
        WHERE d.date >= '{five_years_ago}'
    """
    ahmedabad_data = get_data_from_db('apmc_ahmedabad', q_ahmedabad)

    # 2. Fetch Gondal
    print("Fetching Gondal...")
    q_gondal = f"""
        SELECT 'Gondal', c.commodity_name, p.price_date, p.min_price, p.max_price 
        FROM prices p
        JOIN commodities c ON p.commodity_id = c.id
        WHERE p.price_date >= '{five_years_ago}'
    """
    gondal_data = get_data_from_db('gondalmarket', q_gondal)

    # 3. Fetch Rajkot
    # Based on your table error, we use market_prices and jansi_master
    print("Fetching Rajkot...")
    q_rajkot = f"""
        SELECT 'Rajkot', j.jansi_english_name, m.date, m.lowrate, m.highrate 
        FROM market_prices m
        JOIN jansi_master j ON m.id = j.id
        WHERE m.date >= '{five_years_ago}'
    """
    rajkot_data = get_data_from_db('market', q_rajkot)

    # 4. Insert into Analysis DB
    all_data = ahmedabad_data + gondal_data + rajkot_data
    if not all_data:
        print("No data found to migrate.")
        return

    print(f"Total records found: {len(all_data)}. Inserting...")
    
    try:
        conn = mysql.connector.connect(**db_config, database='internship_analysis')
        cursor = conn.cursor()
        
        insert_query = """
            INSERT INTO unified_market_data 
            (district_name, commodity_name, price_date, min_price, max_price, average_price, year) 
            VALUES (%s, %s, %s, %s, %s, (%s + %s)/2, YEAR(%s))
        """
        
        # Insert in chunks of 1000 to avoid connection reset
        chunk_size = 1000
        for i in range(0, len(all_data), chunk_size):
            chunk = all_data[i:i + chunk_size]
            final_entries = [(r[0], r[1], r[2], r[3], r[4], r[3], r[4], r[2]) for r in chunk]
            cursor.executemany(insert_query, final_entries)
            conn.commit()
            print(f"Inserted {i + len(chunk)} records...")

        print("Success! Migration complete.")
        
    except mysql.connector.Error as err:
        print(f"Final Insertion Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    migrate_data()