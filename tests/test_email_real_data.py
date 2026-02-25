import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils.data_loader import load_data
from utils.notification_service import AlertDispatcher

def test_email_generation():
    print("1. Loading Data...")
    df = load_data()
    print(f"   Loaded {len(df)} records.")
    
    # Filter for a customer with a valid email (from Customer Master)
    # Check for 'email_id' column
    if 'email_id' not in df.columns:
        print("ERROR: 'email_id' column missing. PII Merge failed?")
        return

    # Pick a customer with a real email (not NaN)
    valid_customers = df[df['email_id'].notna() & (df['email_id'] != 'nan')]
    
    if valid_customers.empty:
        print("ERROR: No customers with valid emails found.")
        return

    # Pick the first one
    customer = valid_customers.iloc[0]
    print(f"2. Selected Customer: {customer.get('full_name')} ({customer.get('customer_id')})")
    print(f"   Email: {customer.get('email_id')}")
    
    print("\n3. Generating Alert...")
    try:
        result = AlertDispatcher.send_intervention_alert(customer)
        
        print("\n--- TEST RESULTS ---")
        print(f"Status: {'SUCCESS' if result['email_sent'] else 'FAILED'}")
        print(f"Target Email: {customer.get('email_id')}")
        print(f"Generated Token: {result['token']}")
        # The link is printed by the service, but we can verify logic here
        expected_link = f"http://localhost:8050/customer/intervention?token={customer.get('customer_id')}"
        print(f"Expected Link: {expected_link}")
        
    except Exception as e:
        print(f"TEST FAILED: {e}")

if __name__ == "__main__":
    test_email_generation()
