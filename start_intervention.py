import os
import sys
import subprocess
import time
import threading
from pyngrok import ngrok

# Configuration
PORT = 8051
APP_SCRIPT = "src/intervention_portal.py"

def start_ngrok():
    """Starts ngrok tunnel and sets environment variable."""
    try:
        # Open a HTTP tunnel on the default port 80
        # <NgrokTunnel: "http://<public_sub>.ngrok.io" -> "http://localhost:80">
        public_url = ngrok.connect(PORT).public_url
        print(f"\n[NGROK] Tunnel established at: {public_url}")
        
        # Set environment variable for the subprocess to pick up? 
        # Actually, we need to pass this to the MAIN app (dashboard) if that's where emails are sent from.
        # OR if this script runs the dashboard too?
        # The user said "The Customer Intervention Portal is deployed as an independent standalone Dash application... independent from the internal bank dashboard."
        # AND "Update the current email alert system... when a Relationship Manager sends an alert from the Customer Explorer Dashboard"
        
        # So the Dashboard (running normally) needs to know this URL.
        # We can print it and ask user to set it, OR we can write it to a .env file, OR...
        # For this task, strict automation might be hard if processes are separate.
        # BUT, if we run the DASHBOARD from here too, we can pass it.
        
        # However, the user request focuses on the intervention portal being standalone.
        # Let's write the URL to a temporary file that the dashboard can read, or just print it clearly.
        # Better: Set it as a system environment variable? No, that's process local.
        
        # Strategy: 
        # 1. Start Ngrok.
        # 2. Start Intervention App (PORT 8051).
        # 3. Print the URL and instruction to set `INTERVENTION_BASE_URL` for the main dashboard.
        
        print(f"[INFO] Please set process env var: set INTERVENTION_BASE_URL={public_url}")
        os.environ["INTERVENTION_BASE_URL"] = public_url
        return public_url
    except Exception as e:
        print(f"[ERROR] Ngrok failed: {e}")
        return None

def run_intervention_app():
    """Runs the standalone dash app."""
    print(f"[INFO] Starting Intervention App {APP_SCRIPT}...")
    subprocess.run([sys.executable, APP_SCRIPT], check=True)

if __name__ == "__main__":
    url = start_ngrok()
    if url:
        print(f"[INFO] Intervention Portal Secure Link Base: {url}")
        print("-" * 50)
        
        # Run the app
        run_intervention_app()
