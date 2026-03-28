import sys
import os
from datetime import datetime, timedelta

# Add the project directory to the path so we can import our modules
sys.path.append(os.getcwd())

from core.services.government_api import GovernmentAPIClient

def sync_remaining_data():
    client = GovernmentAPIClient()
    
    # Define the date range: From March 26 to March 28, 2026
    # API format for Agmarknet arrival_date is dd/mm/yyyy
    dates_to_sync = ["26/03/2026", "27/03/2026", "28/03/2026"]
    
    print(f"--- Starting Sync for Remaining Data ({dates_to_sync[0]} to {dates_to_sync[-1]}) ---")
    
    for date_str in dates_to_sync:
        print(f"\nProcessing date: {date_str}")
        try:
            count = client.sync_market_prices(date_filter=date_str)
            print(f"Synced {count} records for {date_str}.")
        except Exception as e:
            print(f"Failed to sync data for {date_str}: {e}")
            
    print("\n--- Sync Process Completed ---")

if __name__ == "__main__":
    sync_remaining_data()
