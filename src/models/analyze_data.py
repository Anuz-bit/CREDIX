import pandas as pd
import os

DATA_DIR = r'project/data/processed'
FILES = ['CUSTOMER_MASTER.csv', 'FEATURE_STORE.csv', 'TRANSACTIONS.csv']

def analyze_file(filename):
    filepath = os.path.join(DATA_DIR, filename)
    print(f"--- Analyzing {filename} ---")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    try:
        df = pd.read_csv(filepath)
        print(f"Shape: {df.shape}")
        print("\nColumns & Types:")
        print(df.dtypes)
        print("\nMissing Values:")
        print(df.isnull().sum())
        print("\nFirst 3 rows:")
        print(df.head(3))
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Error reading {filename}: {e}")

if __name__ == "__main__":
    for f in FILES:
        analyze_file(f)
