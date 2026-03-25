import os
import subprocess
import time
from datetime import datetime

def run_sync():
    """Run all legacy Selenium scrapers for government data"""
    print(f"--- Starting Selenium Scraper Sync at {datetime.now()} ---")
    
    # List of scrapers to run
    scrapers = [
        "scrapers/agmarknet_official.py",
        "scrapers/enam_scraper.py",
        "scrapers/imd_scraper.py"
    ]
    
    for script_base in scrapers:
        script_path = os.path.join(os.getcwd(), script_base)
        if not os.path.exists(script_path):
            print(f"WARNING: {script_path} not found. Skipping...")
            continue
            
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        
        print(f"Executing {script_path}...")
        try:
            result = subprocess.run(["python", script_path], capture_output=True, text=True, env=env)
            if result.returncode == 0:
                print(f"SUCCESS: {script_path} completed.")
                print(result.stdout)
            else:
                print(f"ERROR: {script_path} failed with return code {result.returncode}.")
                print(result.stderr)
        except Exception as e:
            print(f"CRITICAL: Failed to run {script_path}: {e}")

    print(f"--- Finished Sync Task at {datetime.now()} ---\n")

if __name__ == "__main__":
    run_sync()
