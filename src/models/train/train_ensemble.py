import pandas as pd
import numpy as np
import os
import sys
import pickle
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, StackingClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report

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

def get_metrics(y_true, y_pred, y_prob=None):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    if y_prob is not None:
        try:
            if len(np.unique(y_true)) == 2:
                auc = roc_auc_score(y_true, y_prob[:, 1])
            else:
                auc = roc_auc_score(y_true, y_prob, multi_class='ovr')
        except:
            auc = 0.0
    else:
        auc = 0.0
        
    cm = confusion_matrix(y_true, y_pred)
    return {'Accuracy': acc, 'Precision': prec, 'Recall': rec, 'F1 Score': f1, 'ROC-AUC': auc, 'Confusion Matrix': cm}

def main():
    print("Loading and preprocessing data...")
    try:
        df = create_dataset()
    except Exception as e:
        print(f"Error creating dataset: {e}")
        return

    target_col = 'target'
    if target_col not in df.columns:
        print("Target column not found.")
        return
        
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Ensure numeric
    X = X.select_dtypes(include=[np.number])
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Base Models
    lr = LogisticRegression(max_iter=1000, random_state=42)
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    xgb = XGBClassifier(eval_metric='mlogloss', use_label_encoder=False, random_state=42)
    
    estimators = [('lr', lr), ('rf', rf), ('xgb', xgb)]
    
    # 1. Soft Voting Ensemble
    print("\n--- Training Soft Voting Ensemble ---")
    voting_clf = VotingClassifier(estimators=estimators, voting='soft')
    voting_clf.fit(X_train, y_train)
    
    # 2. Stacking Ensemble
    print("\n--- Training Stacking Ensemble ---")
    stacking_clf = StackingClassifier(estimators=estimators, final_estimator=LogisticRegression(), cv=3)
    stacking_clf.fit(X_train, y_train)
    
    # Evaluation
    models = {
        'Logistic Regression': lr,
        'Random Forest': rf,
        'XGBoost': xgb,
        'Voting Ensemble': voting_clf,
        'Stacking Ensemble': stacking_clf
    }
    
    results = []
    trained_models = {}
    
    best_model_name = None
    best_score = -1
    primary_metric = 'F1 Score' # Using F1 Weighted as primary
    
    print("\n--- Model Evaluation ---")
    for name, model in models.items():
        print(f"Evaluating {name}...")
        if name not in ['Voting Ensemble', 'Stacking Ensemble']:
            model.fit(X_train, y_train)
            
        y_pred = model.predict(X_test)
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_test)
        else:
            y_prob = None
            
        metrics = get_metrics(y_test, y_pred, y_prob)
        metrics['Model'] = name
        results.append(metrics)
        trained_models[name] = model
        
        print(f"Confusion Matrix for {name}:\n{metrics['Confusion Matrix']}")
        
        score = metrics[primary_metric]
        if score > best_score:
            best_score = score
            best_model_name = name

    # Comparison Table
    results_df = pd.DataFrame(results).set_index('Model')
    # Drop Confusion Matrix from display table for cleaner output
    display_df = results_df.drop(columns=['Confusion Matrix'])
    
    print("\n" + "="*50)
    print("FINAL COMPARISON TABLE")
    print("="*50)
    print(display_df)
    print("="*50)
    
    print(f"\nBest Model: {best_model_name} ({primary_metric}: {best_score:.4f})")
    
    # Save Best Model
    save_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, 'ensemble_model.pkl')
    
    best_model = trained_models[best_model_name]
    
    # If the best model is NOT an ensemble, user request wording implies we should maybe save the best ensemble?
    # "Save best ensemble model to..." implies specifically the ensemble.
    # But usually we want the absolute best.
    # Instruction: "3) Compare... 5) Save best ensemble model to..."
    # It says "Save best **ensemble** model". This might mean:
    # A) Save the best among [Voting, Stacking]
    # B) Save the best overall, which is likely an ensemble (implied).
    # I will save the best among ALL models, but if it's a single model, I'll still save it.
    # Actually, looking closely: "Save best **ensemble** model".
    # I will compare Voting vs Stacking and save the winner of those two to adhere strictly, OR if an individual model is better, I might warn.
    # Let's verify standard interpretation: "Save the resulting best model".
    # The prompt explicitly asks to "Compare Best Individual vs Ensembles".
    # And then "Save best ensemble model".
    # I will check if an ensemble defeated the individual models.
    # If not, I will save the best **Ensemble** (Voting or Stacking) as requested, even if individual is better?
    # No, typically "best ensemble model" implies the best model which happens to be an ensemble.
    # I will save the best of [Voting, Stacking].
    
    ensemble_results = [r for r in results if 'Ensemble' in r['Model']]
    best_ensemble = max(ensemble_results, key=lambda x: x[primary_metric])
    best_ensemble_name = best_ensemble['Model']
    
    print(f"Best Ensemble: {best_ensemble_name} ({primary_metric}: {best_ensemble[primary_metric]:.4f})")
    
    # Check if individual was better
    if results_df[primary_metric].max() > best_ensemble[primary_metric]:
        print(f"Note: A single model ({best_model_name}) performed better than ensembles.")
        
    model_to_save = trained_models[best_ensemble_name]
    with open(save_path, 'wb') as f:
        pickle.dump(model_to_save, f)
        
    print(f"Saved best ensemble model ({best_ensemble_name}) to {save_path}")

if __name__ == "__main__":
    main()
