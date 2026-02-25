import pandas as pd
import numpy as np
import os
import sys
import pickle
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, make_scorer

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from project.src.preprocessing import create_dataset
except ImportError:
    try:
        from preprocessing import create_dataset
    except ImportError:
         sys.path.append(os.path.dirname(os.path.abspath(__file__)))
         from preprocessing import create_dataset

def get_metrics_report(y_true, y_pred, y_prob=None):
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    
    auc_val = 0.5
    if y_prob is not None:
        try:
            if len(np.unique(y_true)) == 2:
                auc_val = roc_auc_score(y_true, y_prob[:, 1])
            else:
                auc_val = roc_auc_score(y_true, y_prob, multi_class='ovr')
        except:
            auc_val = 'N/A'
            
    return acc, f1, auc_val

def main():
    print("--- 🔄 Step 2 & 3: Correct Data Splitting & Cross-Validation ---")
    
    # 1. Load Data
    print("Loading data...")
    df = create_dataset()
    
    target_col = 'target'
    if target_col not in df.columns:
        print("Target column not found.")
        return

    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # 2. DROP LEAKY FEATURES
    leaky_features = [
        'current_risk_score', 
        'probability_of_default', 
        'risk_trend', 
        'model_confidence_score',
        'regulatory_risk_category' # Safely remove potential proxy
    ]
    
    # Filter only existing columns
    to_drop = [col for col in leaky_features if col in X.columns]
    print(f"\n🚫 Dropping Leaky Features: {to_drop}")
    X = X.drop(columns=to_drop)
    
    # 3. Train-Test Split (Startified, Fixed Random State)
    # Applying split BEFORE scaling
    print("\n[Split] Performing Stratified Train-Test Split (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 4. Define Models & Pipelines
    # Using pipeline to scale within CV folds
    models = {
        'Logistic Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(max_iter=1000, random_state=42))
        ]),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        'XGBoost': XGBClassifier(eval_metric='mlogloss', use_label_encoder=False, random_state=42, n_jobs=-1)
    }
    
    # 5. Cross-Validation (5-Fold Stratified)
    scoring = {
        'accuracy': 'accuracy',
        'f1_macro': 'f1_macro',
        'roc_auc_ovr': 'roc_auc_ovr'
    }
    
    print("\n📊 Performing 5-Fold Stratified Cross-Validation...")
    cv_results_summary = []
    
    for name, model in models.items():
        print(f"   Running CV for {name}...")
        cv_scores = cross_validate(model, X_train, y_train, cv=5, scoring=scoring, n_jobs=-1)
        
        mean_acc = np.mean(cv_scores['test_accuracy'])
        std_acc = np.std(cv_scores['test_accuracy'])
        mean_f1 = np.mean(cv_scores['test_f1_macro'])
        mean_auc = np.mean(cv_scores['test_roc_auc_ovr'])
        
        cv_results_summary.append({
            'Model': name,
            'CV Mean Accuracy': f"{mean_acc:.4f} (+/- {std_acc:.4f})",
            'CV Mean F1': f"{mean_f1:.4f}",
            'CV Mean AUC': f"{mean_auc:.4f}"
        })
        
    print("\n--- Cross-Validation Results ---")
    cv_df = pd.DataFrame(cv_results_summary)
    print(cv_df)
    cv_df.to_csv('cv_results.csv', index=False)
    
    # 6. Final Evaluation on Test Set
    print("\n--- 📊 Step 4: Final Evaluation on Clean Test Set ---")
    test_results = []
    trained_models = {}
    
    for name, model in models.items():
        # Fit on full training data
        model.fit(X_train, y_train)
        trained_models[name] = model
        
        if hasattr(model, 'predict_proba'):
             # Access step inside pipeline if needed, but Pipeline handles predict/predict_proba
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)
        else:
            y_pred = model.predict(X_test)
            y_prob = None
            
        acc, f1, auc_val = get_metrics_report(y_test, y_pred, y_prob)
        
        test_results.append({
            'Model': name,
            'Accuracy': acc,
            'F1 Score': f1,
            'ROC-AUC': auc_val
        })
        
    results_df = pd.DataFrame(test_results)
    print(results_df)

    # 7. Sanity Checks
    print("\n--- 🚨 Step 5: Sanity Checks ---")
    
    # Check 1: Random Target Shuffle
    print("\n[Check 1] Retraining Random Forest with Shuffled Target (Expect ~Random Accuracy)...")
    y_shuffled = np.random.permutation(y_train)
    rf_sanity = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf_sanity.fit(X_train, y_shuffled)
    y_sanity_pred = rf_sanity.predict(X_test)
    sanity_acc = accuracy_score(y_test, y_sanity_pred)
    # Random baseline for 4 classes ~ 25%
    print(f"Sanity Accuracy (Shuffled): {sanity_acc:.4f} (Should be low/baseline)")
    
    # Check 2: Top Feature Removal
    print("\n[Check 2] Removing Top 3 Important Features and Retraining XGBoost...")
    # Get importance from the trained XGBoost (if pipeline, get step)
    xgb_trained = trained_models['XGBoost']
    
    # Get importances
    importances = xgb_trained.feature_importances_
    indices = np.argsort(importances)[::-1]
    top_3_idx = indices[:3]
    top_3_features = X_train.columns[top_3_idx].tolist()
    
    print(f"Removing Top 3 Features: {top_3_features}")
    
    X_train_reduced = X_train.drop(columns=top_3_features)
    X_test_reduced = X_test.drop(columns=top_3_features)
    
    xgb_reduced = XGBClassifier(eval_metric='mlogloss', use_label_encoder=False, random_state=42, n_jobs=-1)
    xgb_reduced.fit(X_train_reduced, y_train)
    y_red_pred = xgb_reduced.predict(X_test_reduced)
    red_acc = accuracy_score(y_test, y_red_pred)
    
    print(f"Accuracy after removing top features: {red_acc:.4f}")
    if red_acc < results_df.loc[results_df['Model']=='XGBoost', 'Accuracy'].values[0] - 0.05:
         print("✅ Performance dropped significantly as expected.")
    else:
         print("⚠️ Performance remained similar. Information redundant or other leaks exist.")

    # Save CSV of results for easy reading if needed
    results_df.to_csv('post_fix_results.csv', index=False)
    print("\nEvaluation Complete.")

if __name__ == "__main__":
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    main()
