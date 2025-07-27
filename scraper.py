import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

# --- Configuration ---
# URL of the page to scrape
URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
# The file where we will store our data
DATA_FILE = "gas_prices.json"

def scrape_gas_prices():
    """
    Scrapes the gas prices from the CityNews website, updates the data file,
    and returns the latest data.
    """
    try:
        # --- 1. Fetch the Webpage ---
        # We send a request to the website to get its HTML content.
        # The headers make our script look like a regular web browser.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        page = requests.get(URL, headers=headers)
        # This will raise an error if the page didn't load correctly (e.g., 404 Not Found)
        page.raise_for_status()

        # --- 2. Parse the HTML ---
        # BeautifulSoup helps us navigate and search the HTML content easily.
        soup = BeautifulSoup(page.content, "html.parser")

        # --- 3. Find the Price Data ---
        # We need to find the specific HTML element that holds the gas prices.
        # Based on our analysis (as of July 2025), the prices are within a 'div'
        # with the class 'gas-price-card_price__BC_7i'. This might change if the website updates its design.
        price_elements = soup.find_all("div", class_="gas-price-card_price__BC_7i")

        if len(price_elements) < 2:
            print("Error: Could not find the expected price elements on the page.")
            return None

        # The first element is tomorrow's price, the second is today's.
        # We extract the text and remove any extra characters like '¢'.
        tomorrow_price_str = price_elements[0].text.strip().replace('¢', '')
        today_price_str = price_elements[1].text.strip().replace('¢', '')

        # Convert the prices to numbers (floats).
        tomorrow_price = float(tomorrow_price_str)
        today_price = float(today_price_str)

        # --- 4. Prepare the Data Entry ---
        # Get today's date in a standard format (YYYY-MM-DD).
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        # The "tomorrow" price from the site is the price for the next calendar day.
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        new_data_entry = {
            "date": tomorrow_date,
            "price": tomorrow_price
        }
        
        print(f"Scraped Data: Date={new_data_entry['date']}, Price={new_data_entry['price']}")

        # --- 5. Read, Update, and Save the Data File ---
        # We use a set to keep track of dates to avoid duplicates.
        existing_dates = set()
        
        # Check if the data file already exists.
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                try:
                    # Load existing data from the file.
                    data = json.load(f)
                    # Populate our set of dates.
                    for entry in data:
                        existing_dates.add(entry['date'])
                except json.JSONDecodeError:
                    # If the file is empty or corrupted, start fresh.
                    data = []
        else:
            # If the file doesn't exist, start with an empty list.
            data = []

        # Add the new entry only if the date is not already in our records.
        if new_data_entry['date'] not in existing_dates:
            data.append(new_data_entry)
            print(f"New entry for {new_data_entry['date']} added.")
        else:
            print(f"Entry for {new_data_entry['date']} already exists. No update needed.")

        # Sort the data by date to keep the file organized.
        data.sort(key=lambda x: x['date'])

        # Write the updated data back to the file.
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
            print(f"Successfully updated {DATA_FILE}")

        return new_data_entry

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    except (IndexError, AttributeError, ValueError) as e:
        # These errors happen if the website's HTML structure has changed.
        print(f"Error parsing the page. The website structure may have changed. Details: {e}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    # This block runs when you execute the script directly (e.g., `python scraper.py`).
    # It's useful for testing.
    scraped_data = scrape_gas_prices()
    if scraped_data:
        print("\nScraping process completed successfully.")
    else:
        print("\nScraping process failed.")
