import json
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

URL = "https://toronto.citynews.ca/toronto-gta-gas-prices/"
DATA_FILE = "gas_prices.json"

# --- Create a directory for debug artifacts ---
DEBUG_DIR = "debug_artifacts"
if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

def run_diagnostic_scrape():
    """
    This is a special diagnostic script. It will try to find the price,
    but more importantly, it will save a screenshot and the HTML content
    of the page for manual analysis.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("--- Starting Diagnostic Scrape ---")
            print(f"--- Navigating to {URL} ---")
            # Wait for the page to be fully loaded, including network requests
            page.goto(URL, wait_until='networkidle', timeout=60000)
            print("Page loaded. Waiting 5 seconds for any final scripts to run...")
            page.wait_for_timeout(5000) # Extra wait time

            # --- Save Diagnostic Files ---
            screenshot_path = os.path.join(DEBUG_DIR, "screenshot.png")
            html_path = os.path.join(DEBUG_DIR, "page_content.html")
            
            print(f"Saving screenshot to {screenshot_path}")
            page.screenshot(path=screenshot_path, full_page=True)
            
            print(f"Saving HTML content to {html_path}")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            
            print("--- Diagnostic files saved. Now attempting to find price... ---")

            # --- Attempt to find the price (this will likely fail, which is okay) ---
            tomorrow_price_selector = "div:has(> h3:has-text('Tomorrow')) h2"
            price_text = page.inner_text(tomorrow_price_selector, timeout=5000) # Short timeout
            
            print(f"SUCCESS: Found price text: {price_text}")
            price = float(price_text.strip().replace('¢', ''))
            
            browser.close()
            return price

        except Exception as e:
            print(f"\n--- SCRIPT FAILED AS EXPECTED ---")
            print(f"Error message: {e}")
            print("This is okay. The important part is that the diagnostic files were saved.")
            browser.close()
            # We will exit with a special code to indicate diagnostics are ready
            exit(99) 

# --- Main Execution ---
if __name__ == "__main__":
    # This script is not intended to succeed, but to produce debug files.
    run_diagnostic_scrape()
