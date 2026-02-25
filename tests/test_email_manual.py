import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils.notification_service import EmailService, SMTP_EMAIL

# --- CONFIGURATION ---
# Change this to the email you want to receive the test at!
TEST_RECIPIENT = "sampada.yanpallewar24@vit.edu" 

def test_manual_email():
    print("--- MANUAL SMTP TEST ---")
    print(f"From: {SMTP_EMAIL}")
    print(f"To:   {TEST_RECIPIENT}")
    
    if TEST_RECIPIENT == "YOUR_PERSONAL_EMAIL@gmail.com":
        print("\n[WARNING] You haven't changed the TEST_RECIPIENT in this script yet.")
        print("Please edit 'tests/test_email_manual.py' and set TEST_RECIPIENT to your actual email.")
        return

    subject = "Credix SMTP Test"
    body = "<h1>Success!</h1><p>Your SMTP configuration is working correctly.</p>"
    
    print("\nSending...")
    success = EmailService.send_email(TEST_RECIPIENT, subject, body)
    
    if success:
        print("\nSUCCESS: Check your inbox!")
    else:
        print("\nFAILED: Check your credentials and console output.")

if __name__ == "__main__":
    test_manual_email()
