import json
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
DATA_FILE = "gas_prices.json"

def find_gas_price_with_browser():
    """
    Final, correct method. First clicks the cookie consent button,
    then finds the 'Tomorrow' card and extracts the price.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("--- Launching Browser ---")
            print(f"--- Navigating to {URL} ---")
            page.goto(URL, wait_until='domcontentloaded', timeout=60000)
            print("Page loaded. Looking for the cookie consent banner...")

            # --- Step 1: Handle the Cookie Banner ---
            cookie_button_selector = "button.consent-ok-btn"
            try:
                # Wait for the "Allow All" button to be visible, with a short timeout
                page.wait_for_selector(cookie_button_selector, timeout=15000)
                print("Cookie banner found. Clicking 'Allow All'.")
                page.click(cookie_button_selector)
                print("Cookie button clicked. Waiting for page to settle...")
                # Wait a moment for the page to reload/settle after the click
                page.wait_for_timeout(5000)
            except Exception as e:
                # If the banner doesn't appear after 15s, assume it's not there and continue.
                print(f"Cookie banner not found or could not be clicked (which is okay). Continuing... Error: {e}")

            # --- Step 2: Scrape the Price ---
            print("Looking for the 'Tomorrow' price card...")
            tomorrow_price_selector = "div:has(> h3:has-text('Tomorrow')) h2"
            
            page.wait_for_selector(tomorrow_price_selector, timeout=30000)
            print("Found the 'Tomorrow' price card.")

            price_text = page.inner_text(tomorrow_price_selector)
            print(f"Successfully extracted price text: {price_text}")
            
            browser.close()
            
            price = float(price_text.strip().replace('¢', ''))
            return price

        except Exception as e:
            print(f"An error occurred during the scrape: {e}")
            # Save a final screenshot on error for debugging
            page.screenshot(path="error_screenshot.png")
            browser.close()
            return None

def update_data_file(price):
    """Updates the JSON file with the new price."""
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    new_entry = {"date": tomorrow_date, "price": price}

    data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try: data = json.load(f)
            except json.JSONDecodeError: pass
    
    existing_dates = {entry['date'] for entry in data}
    if new_entry['date'] not in existing_dates:
        data.append(new_entry)
        data.sort(key=lambda x: x['date'])
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Successfully wrote new entry to {DATA_FILE}")
    else:
        print("Data for tomorrow already exists. No update needed.")

# --- Main Execution ---
if __name__ == "__main__":
    price = find_gas_price_with_browser()
    if price is not None:
        update_data_file(price)
        print("\nProcess completed successfully.")
    else:
        print("\nProcess failed. Could not retrieve price.")
        exit(1)
