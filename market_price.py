import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import sys

# 1. SETUP ENGINES
try:
    # Adjust these connection strings to match your local MySQL setup
    eng_raj = create_engine("mysql+pymysql://root:@localhost/market")
    eng_gon = create_engine("mysql+pymysql://root:@localhost/gondalmarket")
    eng_ahm = create_engine("mysql+pymysql://root:@localhost/apmc_ahmedabad")
    print("✅ Databases connected successfully.")
except Exception as e:
    print(f"❌ Connection Error: {e}")
    sys.exit()

# 2. USER INPUT
print("\n" + "="*40)
# The user can now type the name in any case (e.g., 'wheat' or 'WHEAT')
user_input = input("Enter Commodity Name to search: ").strip()
print("="*40 + "\n")

# 3. FETCH DATA USING CASE-INSENSITIVE SQL
try:
    # Using LOWER() on both the column and the input for a guaranteed match
    
    # Rajkot Query (jansi_master -> jansi_english_name)
    q_raj = f"""
        SELECT mp.date, (mp.lowrate * 5) as raj_price 
        FROM market_prices mp 
        JOIN jansi_master jm ON mp.id = jm.id 
        WHERE LOWER(jm.jansi_english_name) LIKE LOWER('%%{user_input}%%') 
        AND mp.lowrate > 0
    """
    df_raj = pd.read_sql(q_raj, eng_raj)
    
    # Gondal Query (commodities -> commodity_name)
    # Includes a fallback check for Gujarati if the English search fails
    q_gon = f"""
        SELECT p.price_date as date, (p.min_price * 5) as gon_price 
        FROM prices p 
        JOIN commodities c ON p.commodity_id = c.id 
        WHERE LOWER(c.commodity_name) LIKE LOWER('%%{user_input}%%') 
        OR c.commodity_name LIKE '%%ઘઉં%%'
        AND p.min_price > 0
    """
    df_gon = pd.read_sql(q_gon, eng_gon)

    # Ahmedabad Query (commodities -> commodity_name)
    q_ahm = f"""
        SELECT dr.date, dr.min_rate as ahm_price 
        FROM daily_rates dr 
        JOIN commodities c ON dr.commodity_id = c.id 
        WHERE LOWER(c.commodity_name) LIKE LOWER('%%{user_input}%%') 
        AND dr.min_rate > 0
    """
    df_ahm = pd.read_sql(q_ahm, eng_ahm)

    # Standardize Dates
    for df in [df_raj, df_gon, df_ahm]:
        if not df.empty: 
            df['date'] = pd.to_datetime(df['date'])

except Exception as e:
    print(f"❌ Fetch Error: {e}")
    sys.exit()

# 4. MERGE, CLEAN, AND CALCULATE TRENDS
if not df_raj.empty or not df_gon.empty or not df_ahm.empty:
    # Outer join handles different market holidays
    df_merge = pd.merge(df_raj, df_gon, on='date', how='outer')
    df_merge = pd.merge(df_merge, df_ahm, on='date', how='outer').sort_values('date')
    
    # Forward-fill gaps so the graph lines are continuous
    df_merge[['raj_price', 'gon_price', 'ahm_price']] = df_merge[['raj_price', 'gon_price', 'ahm_price']].ffill().bfill()

    # Calculate 7-Day SMA for a professional 'Clean' look
    df_merge['raj_sma'] = df_merge['raj_price'].rolling(window=7).mean()
    df_merge['gon_sma'] = df_merge['gon_price'].rolling(window=7).mean()
    df_merge['ahm_sma'] = df_merge['ahm_price'].rolling(window=7).mean()

    # 5. CONSOLE SUMMARY TABLE
    latest = df_merge.iloc[-1]
    print(f"📊 --- {user_input.upper()} LATEST PRICE REPORT ---")
    print(f"Date: {latest['date'].date()}")
    print(f"{'Market':<12} | {'Price (100kg)':<15} | {'7-Day Trend'}")
    print("-" * 45)
    print(f"{'Rajkot':<12} | ₹{latest['raj_price']:>10.2f}     | ₹{latest['raj_sma']:>8.2f}")
    print(f"{'Gondal':<12} | ₹{latest['gon_price']:>10.2f}     | ₹{latest['gon_sma']:>8.2f}")
    print(f"{'Ahmedabad':<12} | ₹{latest['ahm_price']:>10.2f}     | ₹{latest['ahm_sma']:>8.2f}")

    # 6. CLEAN VISUALIZATION
    plt.figure(figsize=(15, 8))
    
    plt.plot(df_merge['date'], df_merge['raj_sma'], color='#1f77b4', label='Rajkot Trend', linewidth=2.5)
    plt.plot(df_merge['date'], df_merge['gon_sma'], color='#ff7f0e', label='Gondal Trend', linewidth=2.5)
    plt.plot(df_merge['date'], df_merge['ahm_sma'], color='#2ca02c', label='Ahmedabad Trend', linewidth=2.5)
    
    # Shade the variation spread between markets
    plt.fill_between(df_merge['date'], 
                     df_merge[['raj_sma', 'gon_sma', 'ahm_sma']].min(axis=1), 
                     df_merge[['raj_sma', 'gon_sma', 'ahm_sma']].max(axis=1), 
                     color='lightgray', alpha=0.3, label='Market Price Spread')

    plt.title(f'Market Price Comparison: {user_input.title()}', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Price (₹ per 100kg)', fontsize=12)
    plt.legend(loc='best', shadow=True)
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # Save the professional PNG report
    filename = f"report_{user_input.lower().replace(' ', '_')}.png"
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"\n📈 Graph saved as '{filename}'")
    plt.show()

else:
    print(f"❌ No records found for '{user_input}' in any database. Try a different name.")