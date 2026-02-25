import subprocess
import sys
import os
import time

def run_script(script_name):
    print(f"--- Running {script_name} ---")
    start_time = time.time()
    
    # Use same python executable as current process
    cmd = [sys.executable, script_name]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode != 0:
            print(f"Error running {script_name} (Duration: {duration:.2f}s):")
            print(result.stderr)
            return False
        else:
            print(f"Success (Duration: {duration:.2f}s)")
            # Print last few lines of stdout for context
            lines = result.stdout.splitlines()
            if lines:
                print("\n".join(lines[-10:]))
            return True
            
    except Exception as e:
        print(f"Failed to execute {script_name}: {e}")
        return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    scripts = [
        'preprocessing.py',     # Step 1: Data prep
        'train_models.py',      # Step 2: Classic ML models (LR, RF, XGB)
        'train_lstm.py'         # Step 3: Deep learning model (LSTM)
    ]
    
    overall_success = True
    
    for script in scripts:
        script_path = os.path.join(base_dir, script)
        if not os.path.exists(script_path):
            print(f"Script not found: {script_path}")
            overall_success = False
            continue
            
        if not run_script(script_path):
            print(f"Pipeline failed at {script}")
            overall_success = False
            break # Stop pipeline on failure? Yes usually better to stop.

    if overall_success:
        print("\n--- Pipeline Completed Successfully ---")
    else:
        print("\n--- Pipeline Completed with Errors ---")

if __name__ == "__main__":
    main()
