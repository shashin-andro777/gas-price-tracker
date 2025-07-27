import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
DATA_FILE = "gas_prices.json"

def scrape_gas_prices():
    """
    Scrapes the gas prices from the CityNews website using the latest, most robust method.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        page = requests.get(URL, headers=headers)
        page.raise_for_status()

        soup = BeautifulSoup(page.content, "html.parser")

        # Find the main container for the gas price cards. This is a more stable anchor.
        main_container = soup.find("div", class_=lambda c: c and "GasPrices_container" in c)

        if not main_container:
            print("Error: Could not find the main 'GasPrices_container'. Website structure has likely changed.")
            return None

        # Find all the individual price cards within the main container.
        price_cards = main_container.find_all("div", class_=lambda c: c and "gas-price-card" in c)
        
        if not price_cards:
            print("Error: Found main container, but no 'gas-price-card' divs inside. Website structure may have changed.")
            return None

        tomorrow_price_str = None
        
        for card in price_cards:
            heading = card.find("h3")
            if heading and "tomorrow" in heading.text.lower():
                price_element = card.find("h2")
                if price_element:
                    tomorrow_price_str = price_element.text.strip().replace('¢', '')
                    break

        if not tomorrow_price_str:
            print("Error: Could not extract tomorrow's price from the found cards.")
            return None

        tomorrow_price = float(tomorrow_price_str)

        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        new_data_entry = {
            "date": tomorrow_date,
            "price": tomorrow_price
        }
        
        print(f"Scraped Data: Date={new_data_entry['date']}, Price={new_data_entry['price']}")

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

    except Exception as e:
        print(f"An unexpected error occurred during scraping. Details: {e}")
        return None

if __name__ == "__main__":
    if scrape_gas_prices():
        print("\nScraping process completed successfully.")
    else:
        print("\nScraping process failed.")
