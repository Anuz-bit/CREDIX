import os
import sys
import subprocess
import time
import threading
from pyngrok import ngrok

# Configuration
PORTAL_PORT = 8051
DASHBOARD_PORT = 8050
PORTAL_SCRIPT = "src/intervention_portal.py"
DASHBOARD_SCRIPT = "src/app.py"

def start_ngrok():
    """Starts ngrok tunnel for the PORTAL and returns URL."""
    try:
        # Tunnel to the standalone portal (8051)
        public_url = ngrok.connect(PORTAL_PORT).public_url
        print(f"\n[NGROK] Intervention Portal Exposed at: {public_url}")
        return public_url
    except Exception as e:
        print(f"[ERROR] Ngrok failed: {e}")
        return None

def run_process(script, env_vars=None):
    """Runs a python script as a subprocess."""
    print(f"[INFO] Launching {script}...")
    # Merge current env with new vars
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
        
    subprocess.Popen([sys.executable, script], env=env)

if __name__ == "__main__":
    print("="*60)
    print("  CREDIX SYSTEM STARTUP (WITH PUBLIC INTERVENTION PORTAL)")
    print("="*60)

    # 1. Start Ngrok
    public_url = start_ngrok()
    
    if public_url:
        # 2. Prepare Environment
        env_vars = {
            "INTERVENTION_BASE_URL": public_url
        }
        
        # 3. Start Standalone Portal (Port 8051)
        run_process(PORTAL_SCRIPT, env_vars)
        
        # 4. Start Main Dashboard (Port 8050)
        # The dashboard will use INTERVENTION_BASE_URL for generating alert links
        run_process(DASHBOARD_SCRIPT, env_vars)
        
        print("\n" + "-"*60)
        print(f"-> Internal Dashboard: http://localhost:{DASHBOARD_PORT}")
        print(f"-> Public Intervention Portal: {public_url}")
        print(f"-> Secure Links in Emails will start with: {public_url}")
        print("-"*60 + "\n")
        
        # Keep script running to maintain ngrok session
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down system...")
            ngrok.kill()
            sys.exit(0)
    else:
        print("[ERROR] Could not start system because ngrok failed.")
