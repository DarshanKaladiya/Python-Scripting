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
    print(f"✅ Engines connected. Analyzing: {TARGET_COMMODITY}")
except Exception as e:
    print(f"❌ Connection Error: {e}")
    sys.exit()

# 2. FETCH AND CLEAN RAJKOT DATA
try:
    q_raj = f"""
    SELECT mp.date, (mp.lowrate * 5) as raj_price 
    FROM market_prices mp
    JOIN jansi_master jm ON mp.id = jm.id
    WHERE jm.jansi_english_name LIKE '%%{TARGET_COMMODITY}%%' 
    AND mp.lowrate > 0
    """
    df_raj = pd.read_sql(q_raj, eng_raj)
    df_raj['date'] = pd.to_datetime(df_raj['date'])
except Exception as e:
    print(f"❌ Rajkot Error: {e}")

# 3. FETCH AND CLEAN GONDAL DATA
try:
    # Adding Gujarati 'ઘઉં' search for better matching in Gondal DB
    q_gon = f"""
    SELECT p.price_date as date, (p.min_price * 5) as gon_price 
    FROM prices p
    JOIN commodities c ON p.commodity_id = c.id
    WHERE (c.commodity_name LIKE '%%{TARGET_COMMODITY}%%' OR c.commodity_name LIKE '%%ઘઉં%%')
    AND p.min_price > 0
    """
    df_gon = pd.read_sql(q_gon, eng_gon)
    df_gon['date'] = pd.to_datetime(df_gon['date'])
except Exception as e:
    print(f"❌ Gondal Error: {e}")

# 4. MERGE AND CALCULATE TRENDS
if not df_raj.empty and not df_gon.empty:
    df_merge = pd.merge(df_raj, df_gon, on='date', how='inner').sort_values('date')
    
    # 7-Day Moving Average for smoothness
    df_merge['raj_sma'] = df_merge['raj_price'].rolling(window=7).mean()
    df_merge['gon_sma'] = df_merge['gon_price'].rolling(window=7).mean()

    # 5. VISUALIZATION
    plt.figure(figsize=(14, 7))
    
    # Plot Trend Lines
    plt.plot(df_merge['date'], df_merge['raj_sma'], color='#1f77b4', label='Rajkot Trend', linewidth=2.5)
    plt.plot(df_merge['date'], df_merge['gon_sma'], color='#ff7f0e', label='Gondal Trend', linewidth=2.5)
    
    # SHADE THE PRICE GAP
    # This colors the area between the lines to show which is more expensive
    plt.fill_between(df_merge['date'], df_merge['raj_sma'], df_merge['gon_sma'], 
                     where=(df_merge['raj_sma'] >= df_merge['gon_sma']), 
                     interpolate=True, color='blue', alpha=0.1, label='Rajkot Premium')
    
    plt.fill_between(df_merge['date'], df_merge['raj_sma'], df_merge['gon_sma'], 
                     where=(df_merge['raj_sma'] < df_merge['gon_sma']), 
                     interpolate=True, color='orange', alpha=0.1, label='Gondal Premium')

    plt.title(f'Clean Market Comparison: {TARGET_COMMODITY}', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Normalized Price (per 100kg)', fontsize=12)
    plt.legend(frameon=True, shadow=True)
    plt.grid(True, linestyle='--', alpha=0.4)
    
    # Final cleanup and save
    plt.tight_layout()
    plt.savefig(f'final_clean_{TARGET_COMMODITY.lower()}.png', dpi=300)
    print(f"📊 Clean graph with Price Gap saved as 'final_clean_{TARGET_COMMODITY.lower()}.png'")
    plt.show()
else:
    print("❌ Critical Error: Could not find overlapping data for a graph.")