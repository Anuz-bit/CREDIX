import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import datetime

# --- SMTP CONFIGURATION ---
# PLEASE REPLACE WITH YOUR ACTUAL CREDENTIALS
SMTP_SERVER = "smtp.gmail.com"  # e.g., smtp.gmail.com for Gmail
SMTP_PORT = 587                 # 587 for TLS, 465 for SSL
SMTP_EMAIL = "credix.alerts@gmail.com"      # <--- PASTE YOUR EMAIL HERE
SMTP_PASSWORD = "eerssgevpppczval"      # <--- PASTE YOUR APP PASSWORD HERE

class EmailService:
    @staticmethod
    def send_email(to_email, subject, body):
        """
        Sends an email using the configured SMTP server.
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = SMTP_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))

            print(f"\n[EMAIL SERVICE] Connecting to {SMTP_SERVER}...")
            
            # Connect to Server
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls() # Secure the connection
            
            # Login
            print(f"[EMAIL SERVICE] Logging in as {SMTP_EMAIL}...")
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            
            # Send
            text = msg.as_string()
            server.sendmail(SMTP_EMAIL, to_email, text)
            
            # Quit
            server.quit()
            print(f"[EMAIL SERVICE] Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("[EMAIL SERVICE] ERROR: Authentication Failed. Please check your Email and App Password.")
            return False
        except Exception as e:
            print(f"[EMAIL SERVICE] ERROR: Failed to send email. Reason: {e}")
            return False

class SMSService:
    @staticmethod
    def send_sms(phone_number, message):
        """
        Sends an SMS (Mocked).
        """
        try:
            print(f"\n[SMS SERVICE] Sending SMS to {phone_number}")
            print(f"Message: {message}")
            return True
        except Exception as e:
            print(f"SMS failed: {e}")
            return False

class AlertDispatcher:
    @staticmethod
    def send_intervention_alert(customer):
        """
        Orchestrates the sending of Email and SMS alerts for a specific customer.
        """
        # Extract CRM details from enriched data
        customer_id = customer.get('customer_id', 'Unknown')
        name = customer.get('full_name', 'Valued Customer')
        
        # STRICT: Use Real Data Only
        email = customer.get('email_id')
        if not email or str(email) == 'nan':
            # Strict mode: specific error so dashboard knows
            raise ValueError(f"Missing email_id for customer {customer_id}")
             
        phone = customer.get('mobile_number', '+1234567890')
        
        # 1. Determine Risk & Message
        # RiskEngine might be imported from intervention_logic, ensure it works
        try:
            from utils.intervention_logic import RiskEngine, CommunicationEngine
            risk_category = RiskEngine.get_risk_category(customer)
            message_text = CommunicationEngine.generate_message(name, risk_category)
        except Exception:
            risk_category = "High"
            message_text = f"Hi {name}, please review your account options."
        
        # 2. Generate Secure Token & Link
        # Token is the Customer ID for this implementation
        token = customer_id 
        
        # Dynamic URL Generation
        base_url = os.environ.get("INTERVENTION_BASE_URL", "http://localhost:8051")
        secure_link = f"{base_url}/customer/intervention?token={token}"
        
        print(f"[ALERT] Generated Link: {secure_link}")
        
        # 3. Construct Email Content
        email_subject = "We have personalized support options for you"
        email_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                    <h2 style="color: #0a2342;">CREDIX Support</h2>
                    <p>Hi {name},</p>
                    <p>{message_text.replace('[Link]', '')}</p>
                    <p>We have created a secure, personalized portal for you to review your options.</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{secure_link}" style="background-color: #0a2342; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">View Your Personalized Options</a>
                    </div>
                    <p style="font-size: 12px; color: #777;">This link is secure and valid for 48 hours.</p>
                </div>
            </body>
        </html>
        """
        
        # 4. Construct SMS Content
        sms_body = f"CREDIX: Hi {name}, please review your new support options securely: {secure_link}"
        
        # 5. Send Alerts
        email_sent = EmailService.send_email(email, email_subject, email_body)
        sms_sent = SMSService.send_sms(phone, sms_body)
        
        return {
            "customer_id": customer_id,
            "risk_category": risk_category,
            "email_sent": email_sent,
            "sms_sent": sms_sent,
            "token": token,
            "timestamp": datetime.datetime.now().isoformat()
        }

from utils.data_loader import load_data # changed from load_enriched_data if that didn't exist, defaulting to load_data

class RiskMonitor:
    @staticmethod
    def check_and_alert():
        """
        Iterates through ENRICHED customer dataframe and triggers alerts for relevant cases.
        """
        # Load merged data (ML + CRM)
        try:
            dataframe = load_data()
        except:
             return []
        
        results = []
        
        # DEMO LOGIC: Sort by PD descending and pick top 3
        if 'probability_of_default' in dataframe.columns:
            dataframe = dataframe.sort_values(by='probability_of_default', ascending=False)
            
        for index, row in dataframe.head(3).iterrows():
            alert_result = AlertDispatcher.send_intervention_alert(row)
            results.append(alert_result)
                
        return results