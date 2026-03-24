import subprocess
import time
from datetime import datetime

def run_scraper(module_name):
    print(f"--- Starting {module_name} at {datetime.now()} ---")
    try:
        # Run using python -m to handle package structure
        subprocess.run(["python", "-m", f"scrapers.{module_name}"], check=True)
        print(f"--- Finished {module_name} successfully ---\n")
    except Exception as e:
        print(f"--- Error running {module_name}: {e} ---\n")

def official_government_sync():
    """Run all official government data scrapers in sequence"""
    scrapers = [
        "enam_scraper",
        "agmarknet_official",
        "imd_scraper"
    ]
    
    for s in scrapers:
        run_scraper(s)

if __name__ == "__main__":
    official_government_sync()
