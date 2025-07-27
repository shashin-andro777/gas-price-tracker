import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
DATA_FILE = "gas_prices.json"

def find_gas_price():
    """
    This is a much more robust function to find the gas price.
    It looks for the text "tomorrow" on the page and then finds the
    associated price, ignoring most of the HTML structure.
    """
    try:
        print("--- Starting Scrape ---")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        page = requests.get(URL, headers=headers)
        page.raise_for_status()
        print("Successfully fetched the webpage.")

        soup = BeautifulSoup(page.content, "html.parser")
        
        # Find all elements on the page that contain the text "tomorrow", case-insensitive.
        # This is a much more reliable anchor than a CSS class.
        tomorrow_elements = soup.find_all(lambda tag: "tomorrow" in tag.text.lower())
        
        if not tomorrow_elements:
            print("CRITICAL ERROR: Could not find any elements containing the word 'tomorrow'.")
            return None

        print(f"Found {len(tomorrow_elements)} elements containing the word 'tomorrow'. Analyzing them...")

        for element in tomorrow_elements:
            # We assume the price is in a sibling or parent container.
            # Let's search up to two levels of parents for the price element.
            parent = element.parent
            for _ in range(2): # Look in the immediate parent, then the grandparent
                if parent:
                    # The price is usually in a prominent 'h2' tag.
                    price_tag = parent.find('h2')
                    if price_tag and '¢' in price_tag.text:
                        price_str = price_tag.text.strip().replace('¢', '')
                        print(f"SUCCESS: Found price tag: {price_tag.text.strip()}")
                        return float(price_str)
                    parent = parent.parent # Move to the next parent
        
        print("CRITICAL ERROR: Found 'tomorrow' text, but could not find a price tag (h2 with '¢') nearby.")
        return None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
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
    price = find_gas_price()
    if price is not None:
        update_data_file(price)
        print("\nProcess completed successfully.")
    else:
        print("\nProcess failed. Could not retrieve price.")
        # Exit with an error code to make the workflow fail
        exit(1)
