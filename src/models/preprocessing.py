import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import sys
import os

# Add project root to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from project.src.data_loader import load_customer_data, load_feature_store, load_transaction_data
except ImportError:
    # Fallback if running from src directory
    from data_loader import load_customer_data, load_feature_store, load_transaction_data

def preprocess_customer_data(df):
    """
    Preprocess CUSTOMER_MASTER data.
    """
    print("Preprocessing customer data...")
    df = df.copy()
    
    # Drop PII / non-feature columns
    drop_cols = ['full_name', 'mobile_number', 'email_id', 'pan_masked', 'aadhaar_masked', 
                 'dob', 'city', 'state', 'pin_code'] # Dropping high cardinality/PII for now
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    
    # Handle missing values
    # Fill categorical with 'Unknown'
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        df[col] = df[col].fillna('Unknown')
        
    # Fill numerical with median
    num_cols = df.select_dtypes(include=['number']).columns
    for col in num_cols:
        df[col] = df[col].fillna(df[col].median())
        
    # Encode categorical variables
    le_dict = {}
    for col in cat_cols:
        if col != 'customer_id':
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            le_dict[col] = le
            
    return df

def aggregate_transactions(df):
    """
    Aggregate transaction data by customer_id.
    """
    print("Aggregating transaction data...")
    if df.empty:
        return pd.DataFrame(columns=['customer_id'])

    # Basic aggregations
    agg_funcs = {
        'amount_inr': ['sum', 'mean', 'count', 'std'],
        'balance_after_transaction': ['last', 'mean']
    }
    
    # Check if columns exist before aggregating
    for col in agg_funcs.keys():
        if col not in df.columns:
            del agg_funcs[col]
            
    agg_df = df.groupby('customer_id').agg(agg_funcs)
    
    # Flatten multi-level columns
    agg_df.columns = ['txn_' + '_'.join(col).strip() for col in agg_df.columns.values]
    agg_df.reset_index(inplace=True)
    
    # Fill NaNs in aggregated columns (e.g. std dev for single transaction)
    agg_df = agg_df.fillna(0)
    
    return agg_df

def preprocess_feature_store(df):
    """
    Preprocess FEATURE_STORE data.
    """
    print("Preprocessing feature store...")
    df = df.copy()
    
    # Drop non-feature columns
    drop_cols = ['relationship_manager_id', 'model_decision_log_id', 'consent_capture_timestamp', 
                 'last_alert_channel', 'alert_type', 'recommended_plan', 'audit_log_count']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    
    # Target Encoding
    # Assuming 'risk_band' is the target.
    # We will LabelEncode it for now.
    if 'risk_band' in df.columns:
        risk_map = {'Low': 0, 'Moderate': 1, 'Medium': 1, 'High': 2, 'Very High': 3}
        # Use map inside a lambda to handle case sensitivity if needed, or just map
        df['target'] = df['risk_band'].map(risk_map)
        # Drop rows with NaN target
        df = df.dropna(subset=['target'])
        
        # Drop original risk_band
        df = df.drop(columns=['risk_band'])

    # Fill NaNs
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        df[col] = df[col].fillna('Unknown')
        
    num_cols = df.select_dtypes(include=['number']).columns
    for col in num_cols:
        df[col] = df[col].fillna(df[col].median())

    # Encode categoricals
    for col in cat_cols:
        if col != 'customer_id':
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            
    return df

def create_dataset():
    """
    Load, preprocess, and merge data.
    """
    print("Loading data...")
    cust_df = load_customer_data()
    feat_df = load_feature_store()
    txn_df = load_transaction_data()
    
    cust_proc = preprocess_customer_data(cust_df)
    txn_agg = aggregate_transactions(txn_df)
    feat_proc = preprocess_feature_store(feat_df)
    
    print("Merging datasets...")
    # Merge Customer + Features (Target is in Features)
    merged = pd.merge(cust_proc, feat_proc, on='customer_id', how='inner')
    
    # Merge with Transactions
    final_df = pd.merge(merged, txn_agg, on='customer_id', how='left')
    
    # Fill NaNs from left join
    final_df = final_df.fillna(0)
    
    # Drop customer_id
    if 'customer_id' in final_df.columns:
        final_df = final_df.drop(columns=['customer_id'])
        
    return final_df

if __name__ == "__main__":
    try:
        df = create_dataset()
        print(f"Final Data Shape: {df.shape}")
        print("Columns:", df.columns.tolist())
        print(df.head())
        
        # Save for manual inspection
        output_file = os.path.join(os.path.dirname(__file__), 'final_dataset_sample.csv')
        df.head(100).to_csv(output_file, index=False)
        print(f"Saved sample to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
