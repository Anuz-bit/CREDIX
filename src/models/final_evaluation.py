import pandas as pd
import numpy as np
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

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

def final_evaluation():
    # 1. Load and Clean Data
    print("Loading data...")
    df = create_dataset()
    target_col = 'target'
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Drop Leaky Features
    leaky_features = ['current_risk_score', 'probability_of_default', 'risk_trend', 'model_confidence_score', 'regulatory_risk_category']
    to_drop = [col for col in leaky_features if col in X.columns]
    X = X.drop(columns=to_drop)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 2. Define Models
    lr = Pipeline([('scaler', StandardScaler()), ('clf', LogisticRegression(max_iter=1000, random_state=42))])
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    xgb = XGBClassifier(eval_metric='mlogloss', use_label_encoder=False, random_state=42, n_jobs=-1)
    
    # Voting Ensemble
    voting = VotingClassifier(
        estimators=[('lr', lr), ('rf', rf), ('xgb', xgb)],
        voting='soft'
    )
    
    models = {
        'Logistic Regression': lr,
        'Random Forest': rf,
        'XGBoost': xgb,
        'Voting Ensemble': voting
    }
    
    results = []
    
    # Write to file
    with open('final_results.txt', 'w', encoding='utf-8') as f:
        # Redirect stdout to file context
        original_stdout = sys.stdout
        sys.stdout = f
        
        try:
            print("\nEvaluating Models on Final Test Set...")
            for name, model in models.items():
                # Fit (simulating "load")
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_test)
                if hasattr(model, "predict_proba"):
                    y_prob = model.predict_proba(X_test)
                else:
                    y_prob = None
                    
                # Metrics
                acc = accuracy_score(y_test, y_pred)
                prec = precision_score(y_test, y_pred, average='macro', zero_division=0)
                rec = recall_score(y_test, y_pred, average='macro', zero_division=0)
                f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
                
                auc_val = 'N/A'
                if y_prob is not None:
                     if len(np.unique(y_test)) == 2:
                         auc_val = roc_auc_score(y_test, y_prob[:, 1])
                     else:
                         auc_val = roc_auc_score(y_test, y_prob, multi_class='ovr')
                
                # Store for table
                results.append({
                    'Model': name,
                    'Accuracy (%)': f"{acc*100:.2f}%",
                    'Precision': f"{prec:.4f}",
                    'Recall': f"{rec:.4f}",
                    'F1': f"{f1:.4f}",
                    'ROC-AUC': f"{auc_val:.4f}" if isinstance(auc_val, float) else auc_val,
                    '_raw_auc': auc_val if isinstance(auc_val, float) else 0
                })
                
                # Print Individual Result
                print(f"\nModel: {name}")
                print(f"Accuracy: {acc*100:.2f}%")
                print(f"Precision: {prec:.4f}")
                print(f"Recall: {rec:.4f}")
                print(f"F1 Score: {f1:.4f}")
                print(f"ROC-AUC: {auc_val:.4f}" if isinstance(auc_val, float) else f"ROC-AUC: {auc_val}")

            # Comparison Table
            results_df = pd.DataFrame(results)
            display_cols = ['Model', 'Accuracy (%)', 'Precision', 'Recall', 'F1', 'ROC-AUC']
            
            print("\n" + "="*60)
            print("FINAL COMPARISON TABLE")
            print("="*60)
            print(results_df[display_cols].to_string(index=False))
            print("="*60)
            
            # Identify Best
            best_row = results_df.loc[results_df['_raw_auc'].idxmax()]
            print(f"\nBest Overall Model: {best_row['Model']}")
            
        finally:
            sys.stdout = original_stdout
            print("Results written to final_results.txt")

if __name__ == "__main__":
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    final_evaluation()
