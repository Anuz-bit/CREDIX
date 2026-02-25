import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from project.src.preprocessing import create_dataset
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from preprocessing import create_dataset

def audit_leakage():
    output_lines = []
    output_lines.append("--- Data Leakage Audit ---")
    
    print("Loading dataset...")
    try:
        df = create_dataset()
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    target_col = 'target'
    if target_col not in df.columns:
        print("Target column 'target' not found.")
        return

    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # 1. Suspicious Keywords
    suspicious_keywords = ['risk', 'score', 'default', 'prediction', 'probability', 'band', 'class', 'target', 'label']
    suspicious_cols = [col for col in X.columns if any(kw in col.lower() for kw in suspicious_keywords)]
    
    output_lines.append("\n[Suspicious Columns]")
    if suspicious_cols:
        for col in suspicious_cols:
            output_lines.append(f" - {col}")
    else:
        output_lines.append("None found.")

    # 2. Correlations
    output_lines.append("\n[High Correlations (>0.85)]")
    numeric_df = df.select_dtypes(include=[np.number])
    if target_col not in numeric_df.columns:
        numeric_df[target_col] = y
        
    correlations = numeric_df.corr()[target_col].drop(target_col)
    high_corr = correlations[abs(correlations) > 0.85].sort_values(ascending=False)
    
    if not high_corr.empty:
        output_lines.append(high_corr.to_string())
    else:
        output_lines.append("None found.")

    # 3. Feature Importance
    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf.fit(X.fillna(0), y)
    importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    
    output_lines.append("\n[Top 20 Feature Importances]")
    output_lines.append(importances.head(20).to_string())
    
    # Write to file
    with open('audit_results.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    print("Audit results written to audit_results.txt")

if __name__ == "__main__":
    audit_leakage()
