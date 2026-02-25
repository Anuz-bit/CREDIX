import pandas as pd
import os

# Define the data directory relative to the project root or absolute path
# Assuming the script is run from the project root (Haco_o_Hire)
# Robust path finding
def get_data_dir():
    # Helper to find data dir
    # Start from current file: project/src/models/data_loader.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) 
    
    # Check project/data/processed
    path = os.path.join(project_root, 'data', 'processed')
    if os.path.exists(path):
        return path
        
    # Fallback: maybe we are in project/src/models and project root is ./
    path = os.path.join(current_dir, '..', '..', '..', 'data', 'processed')
    if os.path.exists(path):
         return os.path.abspath(path)
         
    # Fallback 2: data/processed relative to cwd
    if os.path.exists(os.path.join('data', 'processed')):
        return os.path.abspath(os.path.join('data', 'processed'))
        
    return path # Return best guess

DATA_DIR = get_data_dir()

def load_csv(filename):
    """
    Load a CSV file from the data directory.
    """
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
         # Try looking in absolute project path if available
         pass # Handled by robust get_data_dir mostly
        
    if not os.path.exists(filepath):
        # Last ditch: try to find it in cwd recursively? No.
        raise FileNotFoundError(f"File not found: {filepath}\nSearch path: {DATA_DIR}")
        
    print(f"Loading {filename} from {filepath}...")
    return pd.read_csv(filepath)

def load_customer_data():
    """Load CUSTOMER_MASTER.csv"""
    return load_csv('CUSTOMER_MASTER.csv')

def load_feature_store():
    """Load FEATURE_STORE.csv"""
    return load_csv('FEATURE_STORE.csv')

def load_transaction_data():
    """Load TRANSACTIONS.csv"""
    return load_csv('TRANSACTIONS.csv')

if __name__ == "__main__":
    # verification
    try:
        df = load_customer_data()
        print(f"Customer Data Shape: {df.shape}")
    except Exception as e:
        print(f"Error: {e}")
