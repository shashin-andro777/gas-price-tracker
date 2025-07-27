import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

# --- Configuration ---
URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
DATA_FILE = "gas_prices.json"

def scrape_gas_prices():
    """
    Scrapes the gas prices from the CityNews website using a more robust method,
    updates the data file, and returns the latest data.
    """
    try:
        # --- 1. Fetch the Webpage ---
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        page = requests.get(URL, headers=headers)
        page.raise_for_status()

        # --- 2. Parse the HTML ---
        soup = BeautifulSoup(page.content, "html.parser")

        # --- 3. Find Price Data (Robust Method) ---
        # Find all the 'gas price card' containers on the page.
        price_cards = soup.find_all("div", class_=lambda c: c and "gas-price-card" in c)

        if not price_cards:
            print("Error: Could not find any 'gas-price-card' containers. Website structure may have changed significantly.")
            return None

        tomorrow_price_str = None
        
        # Loop through the found cards to identify the correct one.
        for card in price_cards:
            # Find the heading within the card.
            heading = card.find("h3")
            if heading and "tomorrow" in heading.text.lower():
                # This is the card we want. Now find the price in it.
                price_element = card.find("h2")
                if price_element:
                    tomorrow_price_str = price_element.text.strip().replace('¢', '')
                    break # Stop looking once we've found it.

        if not tomorrow_price_str:
            print("Error: Found price cards, but could not extract tomorrow's price.")
            return None

        tomorrow_price = float(tomorrow_price_str)

        # --- 4. Prepare the Data Entry ---
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        new_data_entry = {
            "date": tomorrow_date,
            "price": tomorrow_price
        }
        
        print(f"Scraped Data: Date={new_data_entry['date']}, Price={new_data_entry['price']}")

        # --- 5. Read, Update, and Save the Data File ---
        existing_dates = set()
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    for entry in data:
                        existing_dates.add(entry['date'])
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        if new_data_entry['date'] not in existing_dates:
            data.append(new_data_entry)
            print(f"New entry for {new_data_entry['date']} added.")
        else:
            print(f"Entry for {new_data_entry['date']} already exists. No update needed.")

        data.sort(key=lambda x: x['date'])

        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
            print(f"Successfully created/updated {DATA_FILE}")

        return new_data_entry

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during scraping. Details: {e}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    scraped_data = scrape_gas_prices()
    if scraped_data:
        print("\nScraping process completed successfully.")
    else:
        print("\nScraping process failed.")
