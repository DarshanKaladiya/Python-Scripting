import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from io import BytesIO

# 1. Database Connection
def get_data():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="internship_analysis"
        )
        query = "SELECT district_name, commodity_name, price_date, min_price, max_price, average_price, year FROM unified_market_data"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

# 2. UI Setup
st.set_page_config(page_title="APMC Market Analysis", layout="wide")
st.title("🚜 Marketing Yard Comparison Dashboard")

df = get_data()

if not df.empty:
    df['price_date'] = pd.to_datetime(df['price_date'])

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Panels")
    
    # Filter 1: District (Multiselect)
    districts = sorted(df['district_name'].unique())
    selected_districts = st.sidebar.multiselect("1. Select Marketing Yard(s)", options=districts, default=districts)

    # Filter 2: Dynamic Commodity (Changes based on District)
    if selected_districts:
        avail_commodities = sorted(df[df['district_name'].isin(selected_districts)]['commodity_name'].unique())
    else:
        avail_commodities = sorted(df['commodity_name'].unique())
    
    selected_item = st.sidebar.selectbox("2. Select Commodity", avail_commodities)

    # Filter 3: Year Range
    min_year, max_year = int(df['year'].min()), int(df['year'].max())
    year_range = st.sidebar.slider("3. Select Year Range", min_year, max_year, (min_year, max_year))

    # --- MAIN CONTENT ---
    start_year, end_year = year_range
    
    # Global Filtered Data for Download
    full_filtered_df = df[
        (df['district_name'].isin(selected_districts)) & 
        (df['commodity_name'] == selected_item) &
        (df['year'] >= start_year) & (df['year'] <= end_year)
    ].sort_values(by='price_date')

    # Download Button
    if not full_filtered_df.empty:
        csv = full_filtered_df.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"{selected_item}_analysis_{start_year}_{end_year}.csv",
            mime='text/csv',
        )

    # Loop for Yearly Graphs and Tables
    for year in range(start_year, end_year + 1):
        year_df = full_filtered_df[full_filtered_df['year'] == year]
        
        if not year_df.empty:
            st.markdown(f"---")
            st.header(f"📅 Year {year} Analysis: {selected_item}")
            
            # Interactive Graph
            fig = px.line(
                year_df, 
                x='price_date', 
                y='average_price', 
                color='district_name',
                markers=True,
                labels={'price_date': 'Date', 'average_price': 'Price (Avg)', 'district_name': 'Yard'},
                template="plotly_white",
                title=f"Daily Price Trend ({year})"
            )
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            
            # Raw Data Table
            with st.expander(f"View {year} Raw Data Records"):
                st.dataframe(year_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No records found for {selected_item} in {year}.")

else:
    st.warning("No data found in the analysis database. Please run the migration script first.")