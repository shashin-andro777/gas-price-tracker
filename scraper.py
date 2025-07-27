import json
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
DATA_FILE = "gas_prices.json"

def find_gas_price_with_browser():
    """
    Final, correct method. Finds the 'Tomorrow' card specifically and
    extracts the price from within it.
    """
    try:
        with sync_playwright() as p:
            print("--- Launching Browser ---")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"--- Navigating to {URL} ---")
            page.goto(URL, wait_until='domcontentloaded', timeout=60000)
            print("Page loaded. Looking for the 'Tomorrow' price card...")

            # This is a highly specific and robust selector.
            # It finds a div that contains an h3 with the text "Tomorrow",
            # and then finds the h2 (the price) inside that same div.
            tomorrow_price_selector = "div:has(> h3:has-text('Tomorrow')) h2"
            
            # Wait for that specific element to be ready.
            page.wait_for_selector(tomorrow_price_selector, timeout=30000)
            print("Found the 'Tomorrow' price card.")

            # Extract the text from that element.
            price_text = page.inner_text(tomorrow_price_selector)
            print(f"Successfully extracted price text: {price_text}")
            
            browser.close()
            
            # Clean up the string and convert to a number
            price = float(price_text.strip().replace('¢', ''))
            return price

    except Exception as e:
        print(f"An error occurred during the browser-based scrape: {e}")
        return None

def update_data_file(price):
    """Updates the JSON file with the new price."""
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    new_entry = {"date": tomorrow_date, "price": price}

    data = []
    existing_dates = set()
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                for entry in data:
                    existing_dates.add(entry['date'])
            except json.JSONDecodeError:
                pass

    if new_entry['date'] not in existing_dates:
        data.append(new_entry)
        print(f"New entry for {new_entry['date']} added.")
    else:
        print(f"Entry for {new_entry['date']} already exists.")

    data.sort(key=lambda x: x['date'])
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Successfully wrote to {DATA_FILE}")

# --- Main Execution ---
if __name__ == "__main__":
    price = find_gas_price_with_browser()
    if price is not None:
        update_data_file(price)
        print("\nProcess completed successfully.")
    else:
        print("\nProcess failed. Could not retrieve price.")
        exit(1)
