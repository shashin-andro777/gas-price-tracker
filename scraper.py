import json
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
DATA_FILE = "gas_prices.json"

def find_gas_price_with_browser():
    """
    Uses a real browser (via Playwright) to load the page, wait for
    JavaScript to run, and then find the price. This is the definitive method.
    """
    try:
        with sync_playwright() as p:
            print("--- Launching Browser ---")
            browser = p.chromium.launch()
            page = browser.new_page()
            
            print(f"--- Navigating to {URL} ---")
            page.goto(URL, wait_until='networkidle', timeout=60000) # Wait for network to be quiet
            print("Page loaded. Waiting for price element to appear...")

            # This is the crucial step: wait for the element to be visible on the page.
            # We are looking for an h2 tag that contains the '¢' symbol.
            price_selector = "h2:has-text('¢')"
            page.wait_for_selector(price_selector, timeout=30000)
            print("Price element is now visible.")

            # Get all elements that match our price selector
            price_elements = page.query_selector_all(price_selector)
            
            if not price_elements:
                print("CRITICAL ERROR: Waited for price element, but could not query it.")
                browser.close()
                return None

            # The first price on the page is the one for tomorrow.
            tomorrow_price_str = price_elements[0].inner_text()
            print(f"Successfully extracted price text: {tomorrow_price_str}")
            
            browser.close()
            
            # Clean up the string and convert to a number
            price = float(tomorrow_price_str.strip().replace('¢', ''))
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
