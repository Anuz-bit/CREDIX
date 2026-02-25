import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, roc_auc_score
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from project.src.preprocessing import create_dataset
except ImportError:
    # Fallback
    try:
        from preprocessing import create_dataset
    except ImportError:
         sys.path.append(os.path.dirname(os.path.abspath(__file__)))
         from preprocessing import create_dataset

def train_sklearn_models(X_train, y_train):
    print("Training Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    
    return {'LogisticRegression': lr, 'RandomForest': rf}

def train_xgboost(X_train, y_train):
    print("Training XGBoost...")
    xgb = XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42)
    xgb.fit(X_train, y_train)
    return xgb

def evaluate_models(models, X_test, y_test):
    results = {}
    for name, model in models.items():
        print(f"\n--- Evaluating {name} ---")
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        try:
            if hasattr(model, "predict_proba"):
                y_prob = model.predict_proba(X_test)
                if len(np.unique(y_test)) == 2:
                     auc = roc_auc_score(y_test, y_prob[:, 1])
                else:
                     auc = roc_auc_score(y_test, y_prob, multi_class='ovr')
            else:
                auc = 'N/A'
        except Exception as e:
            print(f"AUC calculation failed: {e}")
            auc = 'N/A'
            
        print(f"Accuracy: {acc:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print(f"AUC-ROC: {auc}")
        print(classification_report(y_test, y_pred))
        
        results[name] = {'Accuracy': acc, 'F1': f1, 'AUC': auc}
        
    return results

def plot_feature_importance(model, feature_names, filename='feature_importance.png'):
    print(f"Plotting feature importance for {type(model).__name__}...")
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importances = np.abs(model.coef_[0])
    else:
        print("Model does not expose feature importances.")
        return

    indices = np.argsort(importances)[::-1]
    top_n = 20
    top_indices = indices[:top_n]
    
    plt.figure(figsize=(10, 8))
    plt.title(f"Top {top_n} Feature Importances - {type(model).__name__}")
    plt.barh(range(top_n), importances[top_indices], align="center")
    plt.yticks(range(top_n), [feature_names[i] for i in top_indices])
    plt.gca().invert_yaxis()
    plt.tight_layout()
    
    # Save to project root or data directory
    output_path = os.path.join(project_root, 'project', filename)
    plt.savefig(output_path)
    print(f"Saved feature importance plot to {output_path}")

def main():
    print("Preparing data pipeline...")
    try:
        df = create_dataset()
    except Exception as e:
        print(f"Error creating dataset: {e}")
        return
    
    # Define features and target
    target_col = 'target'
    if target_col not in df.columns:
        raise ValueError("Target column 'target' not found in dataset.")
        
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Ensure all features are numeric
    X = X.select_dtypes(include=[np.number])
    
    # Split data
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train models
    print("\nStarting Model Training...")
    models = train_sklearn_models(X_train, y_train)
    
    try:
        xgb_model = train_xgboost(X_train, y_train)
        models['XGBoost'] = xgb_model
    except Exception as e:
        print(f"XGBoost training failed (check installation): {e}")

    # Evaluate
    evaluate_models(models, X_test, y_test)
    
    # Feature importance
    if 'XGBoost' in models:
        plot_feature_importance(models['XGBoost'], X.columns, 'xgb_feature_importance.png')
    
    if 'RandomForest' in models:
        plot_feature_importance(models['RandomForest'], X.columns, 'rf_feature_importance.png')

if __name__ == "__main__":
    main()
