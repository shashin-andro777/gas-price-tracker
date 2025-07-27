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
            "email": "sx.pandya@gmail.com" # Your verified sender email
        },
        "to": [{"email": recipient_email}],
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
        response.raise_for_status()
        print(f"Successfully sent email to {recipient_email}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending email to {recipient_email}: {e}")
        if e.response is not None:
            print(f"Response from Brevo: {e.response.text}")

def main():
    """
    Main function to orchestrate the enhanced email sending process.
    """
    print("--- Starting Enhanced Email Notification Script ---")
    
    # --- 1. Load Secrets ---
    try:
        brevo_api_key = os.environ['BREVO_API_KEY']
        firebase_service_account_json = os.environ['FIREBASE_SERVICE_ACCOUNT']
    except KeyError as e:
        print(f"FATAL ERROR: Missing environment variable: {e}.")
        return

    # --- 2. Initialize Firebase ---
    try:
        service_account_info = json.loads(firebase_service_account_json)
        cred = credentials.Certificate(service_account_info)
        # Check if the app is already initialized to prevent errors on re-runs
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize Firebase Admin SDK: {e}")
        return

    # --- 3. Get Gas Prices and Calculate Trend ---
    try:
        with open('gas_prices.json', 'r') as f:
            gas_data = json.load(f)
        
        if len(gas_data) < 2:
            print("Not enough data for a price comparison. Need at least 2 days.")
            return

        # Get tomorrow's price (the last entry) and today's price (the second to last)
        tomorrow_entry = gas_data[-1]
        today_entry = gas_data[-2]
        
        tomorrow_price = tomorrow_entry['price']
        today_price = today_entry['price']
        
        date_obj = datetime.strptime(tomorrow_entry['date'], "%Y-%m-%d")
        formatted_date = date_obj.strftime("%A, %B %d, %Y")
        
        # Calculate the difference
        difference = tomorrow_price - today_price
        
        # Build the comparison and trend strings
        comparison_text = ""
        trend_line = ""
        color = "#757575" # Grey for no change

        if difference > 0:
            color = "#D32F2F" # Red for price increase
            comparison_text = f"This is <strong>{difference:.1f}¢ higher</strong> than today's price."
            trend_line = f"{today_price:.1f}¢ → {tomorrow_price:.1f}¢ <span style='color: {color};'>▲</span>"
        elif difference < 0:
            color = "#388E3C" # Green for price decrease
            comparison_text = f"This is <strong>{abs(difference):.1f}¢ lower</strong> than today's price."
            trend_line = f"{today_price:.1f}¢ → {tomorrow_price:.1f}¢ <span style='color: {color};'>▼</span>"
        else:
            comparison_text = "The price is <strong>unchanged</strong> from today."
            trend_line = f"{today_price:.1f}¢ → {tomorrow_price:.1f}¢ <span style='color: {color};'>▬</span>"
            
        print(f"Price for {formatted_date}: {tomorrow_price}¢. {comparison_text}")

    except Exception as e:
        print(f"FATAL ERROR: Could not read or process gas_prices.json: {e}")
        return

    # --- 4. Get Subscriber List ---
    try:
        subscribers_ref = db.collection('subscribers')
        docs = subscribers_ref.stream()
        subscribers = [doc.to_dict()['email'] for doc in docs]
        
        if not subscribers:
            print("No subscribers found. Exiting.")
            return
            
        print(f"Found {len(subscribers)} subscribers to notify.")
    except Exception as e:
        print(f"FATAL ERROR: Could not fetch subscribers from Firestore: {e}")
        return

    # --- 5. Construct and Send Enhanced Emails ---
    subject = f"Gas Price Alert for {formatted_date}: {tomorrow_price:.1f}¢"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .header {{ background-color: #0d47a1; color: #ffffff; padding: 20px; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px; }}
            .content {{ padding: 30px; text-align: center; }}
            .price {{ font-size: 48px; font-weight: bold; color: {color}; margin: 10px 0; }}
            .comparison {{ font-size: 16px; color: #333333; margin-top: 5px; }}
            .trend {{ font-size: 18px; color: #555555; margin-top: 20px; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
            .footer {{ font-size: 12px; color: #888888; text-align: center; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>GTA Gas Price Alert</h1>
            </div>
            <div class="content">
                <p>The predicted average gas price for <strong>{formatted_date}</strong> is:</p>
                <div class="price">{tomorrow_price:.1f}¢</div>
                <div class="comparison">{comparison_text}</div>
                <div class="trend">{trend_line}</div>
            </div>
            <div class="footer">
                <p>To unsubscribe, please visit the <a href="https://gas-price-tracker-sigma.vercel.app/">Gas Price Tracker website</a>, log in, and click "Unsubscribe".</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    for email in subscribers:
        send_email(brevo_api_key, email, subject, html_content)
        
    print("--- Enhanced Email Notification Script Finished ---")

if __name__ == "__main__":
    main()
