import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import sys

# 1. SETUP ENGINES
try:
    eng_raj = create_engine("mysql+pymysql://root:@localhost/market")
    eng_gon = create_engine("mysql+pymysql://root:@localhost/gondalmarket")
    eng_ahm = create_engine("mysql+pymysql://root:@localhost/apmc_ahmedabad")
    print("✅ Databases connected successfully.")
except Exception as e:
    print(f"❌ Connection Error: {e}")
    sys.exit()

while True:
    # 2. INTERACTIVE USER INPUT
    print("\n" + "="*50)
    user_input = input("Enter Commodity (e.g., Groundnut, Cotton) or 'exit': ").strip()
    print("="*50 + "\n")

    if user_input.lower() == 'exit':
        break

    # 3. FETCH DATA (Standardized search across all 3 databases)
    try:
        q_raj = f"SELECT mp.date, (mp.lowrate * 5) as price FROM market_prices mp JOIN jansi_master jm ON mp.id = jm.id WHERE (LOWER(jm.jansi_english_name) LIKE LOWER('%%{user_input}%%') OR jm.jansi_gujarati_name LIKE '%%{user_input}%%') AND mp.lowrate > 0"
        q_gon = f"SELECT p.price_date as date, (p.min_price * 5) as price FROM prices p JOIN commodities c ON p.commodity_id = c.id WHERE (LOWER(c.commodity_name) LIKE LOWER('%%{user_input}%%') OR c.commodity_name LIKE '%%મગફળી%%') AND p.min_price > 0"
        q_ahm = f"SELECT dr.date, dr.min_rate as price FROM daily_rates dr JOIN commodities c ON dr.commodity_id = c.id WHERE (LOWER(c.commodity_name) LIKE LOWER('%%{user_input}%%') OR c.commodity_name LIKE '%%MAGFALI%%') AND dr.min_rate > 0"

        df_raj = pd.read_sql(q_raj, eng_raj).assign(Market='Rajkot')
        df_gon = pd.read_sql(q_gon, eng_gon).assign(Market='Gondal')
        df_ahm = pd.read_sql(q_ahm, eng_ahm).assign(Market='Ahmedabad')

        df_all = pd.concat([df_raj, df_gon, df_ahm])
        if df_all.empty:
            print(f"❌ No records found for '{user_input}'.")
            continue
        
        df_all['date'] = pd.to_datetime(df_all['date'])
        # Pivot and clean for a smooth graph
        df_pivot = df_all.pivot_table(index='date', columns='Market', values='price').ffill().bfill()
        # 7-Day Smoothing
        df_smooth = df_pivot.rolling(window=7, min_periods=1).mean()

    except Exception as e:
        print(f"❌ SQL/Processing Error: {e}")
        continue

    # 4. CHEAPEST YARD COMPARISON
    latest = df_smooth.iloc[-1]
    cheapest_yard = latest.idxmin()
    expensive_yard = latest.idxmax()
    savings = latest.max() - latest.min()

    print(f"--- 📊 {user_input.upper()} ANALYSIS ---")
    for yard in df_smooth.columns:
        print(f"📍 {yard:<12}: ₹{latest[yard]:>8.2f} /100kg")
    
    print("-" * 50)
    print(f"💰 Savings: ₹{savings:.2f} per 100kg (Buy at {cheapest_yard})")
    print("-" * 50)

    # 5. GENERATE CLEAN GRAPH
    plt.figure(figsize=(12, 6))
    for market in df_smooth.columns:
        plt.plot(df_smooth.index, df_smooth[market], label=f"{market} (Trend)", linewidth=2.5)
    
    # Highlight the price gap
    plt.fill_between(df_smooth.index, df_smooth.min(axis=1), df_smooth.max(axis=1), color='gray', alpha=0.1)

    plt.title(f'Market Price Comparison: {user_input.title()}', fontsize=14, fontweight='bold')
    plt.ylabel('Normalized Price (₹ per 100kg)')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend()
    plt.tight_layout()
    plt.show()