import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
DATA_FILE = "gas_prices.json"

def get_price_from_text():
    """
    Final and correct method. Scrapes the static text prediction,
    bypassing all anti-bot measures.
    """
    try:
        print("--- Starting Final Text-Based Scrape ---")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        page = requests.get(URL, headers=headers)
        page.raise_for_status()
        print("Successfully fetched the webpage.")

        soup = BeautifulSoup(page.content, "html.parser")

        # Find the specific div containing the prediction text.
        prediction_div = soup.find("div", class_="gas-prices-section")
        
        if not prediction_div:
            print("CRITICAL ERROR: Could not find the 'gas-prices-section' div.")
            return None, None

        prediction_text = prediction_div.get_text()
        print(f"Found prediction text: {prediction_text.strip()}")

        # Use regular expressions to find the price and date.
        price_match = re.search(r'(\d+\.\d+)\s*cent\(s\)\/litre', prediction_text)
        date_match = re.search(r'on\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})', prediction_text)

        if not price_match:
            print("CRITICAL ERROR: Could not find the price in the text.")
            return None, None
        
        if not date_match:
            print("CRITICAL ERROR: Could not find the date in the text.")
            return None, None

        price = float(price_match.group(1))
        # Reconstruct the date from the matched parts.
        date_str = f"{date_match.group(1)} {date_match.group(2)} {date_match.group(3)}"
        date_obj = datetime.strptime(date_str, "%B %d %Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")

        print(f"Successfully extracted Price: {price}, Date: {formatted_date}")
        return price, formatted_date

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None

def update_data_file(price, date):
    """Updates the JSON file with the new price and date."""
    new_entry = {"date": date, "price": price}

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
        print("Data for this date already exists. No update needed.")

# --- Main Execution ---
if __name__ == "__main__":
    price, date = get_price_from_text()
    if price is not None and date is not None:
        update_data_file(price, date)
        print("\nProcess completed successfully.")
    else:
        print("\nProcess failed. Could not retrieve data.")
        exit(1)
