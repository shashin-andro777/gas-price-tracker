import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

def send_email(api_key, recipient_email, subject, html_content):
    """
    Sends an email using the Brevo (Sendinblue) API.
    """
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {
            "name": "GTA Gas Prices",
            "email": "noreply@gaspricetracker.com" # This can be a no-reply address
        },
        "to": [
            {
                "email": recipient_email
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status() # Raise an error for bad status codes (4xx or 5xx)
        print(f"Successfully sent email to {recipient_email}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending email to {recipient_email}: {e}")

def main():
    """
    Main function to orchestrate the email sending process.
    """
    print("--- Starting Email Notification Script ---")
    
    # --- 1. Load Secrets from Environment Variables ---
    try:
        brevo_api_key = os.environ['BREVO_API_KEY']
        firebase_service_account_json = os.environ['FIREBASE_SERVICE_ACCOUNT']
    except KeyError as e:
        print(f"FATAL ERROR: Missing environment variable: {e}. Ensure secrets are set in GitHub Actions.")
        return

    # --- 2. Initialize Firebase Admin SDK ---
    try:
        service_account_info = json.loads(firebase_service_account_json)
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize Firebase Admin SDK: {e}")
        return

    # --- 3. Get Latest Gas Price ---
    try:
        with open('gas_prices.json', 'r') as f:
            gas_data = json.load(f)
        
        if not gas_data:
            print("gas_prices.json is empty. No email to send.")
            return

        latest_price_entry = gas_data[-1] # The last entry is the latest
        price = latest_price_entry['price']
        date_str = latest_price_entry['date']
        
        # Format the date for display (e.g., "Saturday, July 26, 2025")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%A, %B %d, %Y")
        
        print(f"Latest price found for {formatted_date}: {price}¢")
    except (FileNotFoundError, IndexError, KeyError) as e:
        print(f"FATAL ERROR: Could not read or parse gas_prices.json: {e}")
        return

    # --- 4. Get Subscriber List from Firestore ---
    try:
        subscribers_ref = db.collection('subscribers')
        docs = subscribers_ref.stream()
        subscribers = [doc.to_dict()['email'] for doc in docs]
        
        if not subscribers:
            print("No subscribers found in the database. Exiting.")
            return
            
        print(f"Found {len(subscribers)} subscribers to notify.")
    except Exception as e:
        print(f"FATAL ERROR: Could not fetch subscribers from Firestore: {e}")
        return

    # --- 5. Construct and Send Emails ---
    subject = f"Gas Price Alert for {formatted_date}"
    html_content = f"""
    <html>
    <body>
        <h1>GTA Gas Price Alert</h1>
        <p>The predicted average gas price for <strong>{formatted_date}</strong> is:</p>
        <p style="font-size: 24px; font-weight: bold;">{price}¢ / litre</p>
        <hr>
        <p style="font-size: 12px; color: #888;">
            To unsubscribe, please visit the <a href="https://gas-price-tracker-sigma.vercel.app/">Gas Price Tracker website</a>, log in, and click "Unsubscribe".
        </p>
    </body>
    </html>
    """
    
    for email in subscribers:
        send_email(brevo_api_key, email, subject, html_content)
        
    print("--- Email Notification Script Finished ---")


if __name__ == "__main__":
    main()
