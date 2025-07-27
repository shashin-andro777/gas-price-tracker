import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
DATA_FILE = "gas_prices.json"

def find_gas_price():
    """
    Final, simple approach. Finds all prices on the page and takes the first one.
    """
    try:
        print("--- Starting Final Scrape Attempt ---")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        page = requests.get(URL, headers=headers)
        page.raise_for_status()
        print("Successfully fetched the webpage.")

        soup = BeautifulSoup(page.content, "html.parser")
        
        # Find all h2 tags that contain the '¢' symbol. These are our price candidates.
        price_candidates = soup.find_all('h2', string=lambda text: text and '¢' in text)
        
        if not price_candidates:
            print("CRITICAL ERROR: Could not find any price tags (h2 with '¢') on the page.")
            return None

        print(f"Found {len(price_candidates)} price candidates.")
        for i, candidate in enumerate(price_candidates):
            print(f"  Candidate {i+1}: {candidate.text.strip()}")

        # The first price found on the page is always the "tomorrow" price.
        first_price_str = price_candidates[0].text.strip().replace('¢', '')
        
        print(f"Successfully extracted tomorrow's price: {first_price_str}")
        return float(first_price_str)

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
        exit(1)
