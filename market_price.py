import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import sys

# --- CONFIGURATION ---
TARGET_COMMODITY = "Wheat" 
# ---------------------

# 1. SETUP ENGINES
try:
    eng_raj = create_engine("mysql+pymysql://root:@localhost/market")
    eng_gon = create_engine("mysql+pymysql://root:@localhost/gondalmarket")
    eng_ahm = create_engine("mysql+pymysql://root:@localhost/apmc_ahmedabad")
    print(f"✅ Engines connected. Analyzing: {TARGET_COMMODITY}")
except Exception as e:
    print(f"❌ Connection Error: {e}")
    sys.exit()

# 2. FETCH DATA (Using discovered columns from your .sql files)
try:
    # Rajkot
    q_raj = f"SELECT mp.date, (mp.lowrate * 5) as raj_price FROM market_prices mp JOIN jansi_master jm ON mp.id = jm.id WHERE jm.jansi_english_name LIKE '%%{TARGET_COMMODITY}%%' AND mp.lowrate > 0"
    df_raj = pd.read_sql(q_raj, eng_raj)
    
    # Gondal (with Gujarati support)
    q_gon = f"SELECT p.price_date as date, (p.min_price * 5) as gon_price FROM prices p JOIN commodities c ON p.commodity_id = c.id WHERE (c.commodity_name LIKE '%%{TARGET_COMMODITY}%%' OR c.commodity_name LIKE '%%ઘઉં%%') AND p.min_price > 0"
    df_gon = pd.read_sql(q_gon, eng_gon)

    # Ahmedabad
    q_ahm = f"SELECT dr.date, dr.min_rate as ahm_price FROM daily_rates dr JOIN commodities c ON dr.commodity_id = c.id WHERE c.commodity_name LIKE '%%{TARGET_COMMODITY}%%' AND dr.min_rate > 0"
    df_ahm = pd.read_sql(q_ahm, eng_ahm)

    # Convert dates
    for df in [df_raj, df_gon, df_ahm]:
        if not df.empty: df['date'] = pd.to_datetime(df['date'])
        
except Exception as e:
    print(f"❌ Fetch Error: {e}")
    sys.exit()

# 3. ROBUST MERGING & CLEANING
if not df_raj.empty or not df_gon.empty or not df_ahm.empty:
    # Outer join ensures we keep dates even if some yards are closed
    df_merge = pd.merge(df_raj, df_gon, on='date', how='outer')
    df_merge = pd.merge(df_merge, df_ahm, on='date', how='outer').sort_values('date')
    
    # Fill gaps (ffill carries the last known price forward)
    df_merge[['raj_price', 'gon_price', 'ahm_price']] = df_merge[['raj_price', 'gon_price', 'ahm_price']].ffill().bfill()

    # Calculate 7-Day Moving Averages for a Clean Trend
    df_merge['raj_sma'] = df_merge['raj_price'].rolling(window=7).mean()
    df_merge['gon_sma'] = df_merge['gon_price'].rolling(window=7).mean()
    df_merge['ahm_sma'] = df_merge['ahm_price'].rolling(window=7).mean()

    # 4. LATEST PRICE SUMMARY TABLE
    latest = df_merge.iloc[-1]
    summary_data = {
        "Market Yard": ["Rajkot", "Gondal", "Ahmedabad"],
        "Latest Date": [latest['date'].date()] * 3,
        "Current Price (100kg)": [latest['raj_price'], latest['gon_price'], latest['ahm_price']],
        "7-Day Trend Avg": [latest['raj_sma'], latest['gon_sma'], latest['ahm_sma']]
    }
    df_summary = pd.DataFrame(summary_data)
    
    print("\n--- 📊 LATEST PRICE SUMMARY ---")
    print(df_summary.to_string(index=False))
    df_summary.to_csv("market_summary_report.csv", index=False)
    print("💾 Summary saved to 'market_summary_report.csv'\n")

    # 5. CLEAN VISUALIZATION
    plt.figure(figsize=(15, 8))
    
    # Plot Trend Lines
    plt.plot(df_merge['date'], df_merge['raj_sma'], color='#1f77b4', label='Rajkot Trend', linewidth=3)
    plt.plot(df_merge['date'], df_merge['gon_sma'], color='#ff7f0e', label='Gondal Trend', linewidth=3)
    plt.plot(df_merge['date'], df_merge['ahm_sma'], color='#2ca02c', label='Ahmedabad Trend', linewidth=3)
    
    # Shade the gap between the highest and lowest market
    plt.fill_between(df_merge['date'], df_merge[['raj_sma', 'gon_sma', 'ahm_sma']].min(axis=1), 
                     df_merge[['raj_sma', 'gon_sma', 'ahm_sma']].max(axis=1), 
                     color='lightgray', alpha=0.2, label='Market Variation')

    plt.title(f'Clean 3-Way Market Price Trend: {TARGET_COMMODITY}', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Normalized Price (INR per 100kg)', fontsize=12)
    plt.legend(loc='best', shadow=True)
    plt.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(f'final_report_{TARGET_COMMODITY.lower()}.png', dpi=300)
    print(f"📈 Professional graph saved as 'final_report_{TARGET_COMMODITY.lower()}.png'")
    plt.show()

else:
    print(f"❌ No records found for '{TARGET_COMMODITY}' in any of the databases.")