import pandas as pd
import numpy as np
import os
import sys
import pickle
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report, roc_curve, auc
from sklearn.preprocessing import label_binarize
from sklearn.model_selection import train_test_split

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
    prec = precision_score(y_true, y_pred, average='macro', zero_division=0) # Macro as requested
    rec = recall_score(y_true, y_pred, average='macro', zero_division=0) # Macro as requested
    f1 = f1_score(y_true, y_pred, average='macro', zero_division=0) # Macro as requested
    
    auc_val = 'N/A'
    if y_prob is not None:
        try:
            if len(np.unique(y_true)) == 2:
                auc_val = roc_auc_score(y_true, y_prob[:, 1])
            else:
                auc_val = roc_auc_score(y_true, y_prob, multi_class='ovr')
        except Exception as e:
            print(f"AUC Error: {e}")
            auc_val = 'N/A'
    
    cm = confusion_matrix(y_true, y_pred)
    return {'Accuracy': acc, 'Precision': prec, 'Recall': rec, 'F1 Score': f1, 'ROC-AUC': auc_val, 'Confusion Matrix': cm}

def plot_roc_curve(y_test, y_prob, model_name, n_classes):
    # Retrieve project root for saving
    save_path = os.path.join(project_root, 'project', f'roc_curve_{model_name.replace(" ", "_")}.png')
    
    if y_prob is None:
        return

    # Binarize labels
    y_test_bin = label_binarize(y_test, classes=range(n_classes))
    
    plt.figure(figsize=(8, 6))
    
    # Compute ROC curve and ROC area for each class
    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_prob[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # Compute micro-average ROC curve and ROC area
    fpr["micro"], tpr["micro"], _ = roc_curve(y_test_bin.ravel(), y_prob.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

    plt.plot(fpr["micro"], tpr["micro"],
             label='micro-average ROC curve (area = {0:0.2f})'
                   ''.format(roc_auc["micro"]),
             color='deeppink', linestyle=':', linewidth=4)

    colors = ['aqua', 'darkorange', 'cornflowerblue', 'green']
    for i, color in zip(range(n_classes), colors):
        if i < len(colors): # Safety check
            plt.plot(fpr[i], tpr[i], color=color, lw=2,
                     label='ROC curve of class {0} (area = {1:0.2f})'
                     ''.format(i, roc_auc[i]))

    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC Curve - {model_name}')
    plt.legend(loc="lower right")
    plt.savefig(save_path)
    print(f"Saved ROC curve to {save_path}")
    plt.close()

def main():
    print("Loading data...")
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
    X = X.select_dtypes(include=[np.number])
    
    # Recreate split with same random state
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    n_classes = len(np.unique(y_test))
    
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'ensemble_model.pkl')
    if not os.path.exists(model_path):
        print(f"Model file not found: {model_path}")
        return
        
    print(f"Loading ensemble model from {model_path}...")
    with open(model_path, 'rb') as f:
        ensemble_model = pickle.load(f)
        
    models_to_evaluate = {}
    
    # Check if VotingClassifier
    if hasattr(ensemble_model, 'estimators_'):
        print(f"Loaded {type(ensemble_model).__name__}. Extracting base estimators...")
        # Add the ensemble itself
        models_to_evaluate['Voting Ensemble'] = ensemble_model
        
        # Extract base estimators
        # For VotingClassifier, estimators_ is a list of fitted estimators
        for est in ensemble_model.estimators_:
            name = type(est).__name__
            if name == 'LogisticRegression':
                models_to_evaluate['Logistic Regression'] = est
            elif name == 'RandomForestClassifier':
                models_to_evaluate['Random Forest'] = est
            elif name == 'XGBClassifier':
                models_to_evaluate['XGBoost'] = est
    else:
        print(f"Loaded model is {type(ensemble_model).__name__}, not a VotingClassifier. Cannot easily extract base models without retraining.")
        models_to_evaluate['Saved Model'] = ensemble_model

    # Stacking and LSTM Not Available
    print("Note: Stacking Ensemble and LSTM models were not saved or failed to train. Skipping evaluation for them.")
    
    results = []
    best_model_name = None
    best_score = -1
    primary_metric = 'ROC-AUC' # Using AUC as primary for selection as per prompt implication ("based on ROC-AUC and F1")
    
    print("\n" + "="*50)
    print("MODEL PERFORMANCE EVALUATION")
    print("="*50)
    
    for name, model in models_to_evaluate.items():
        print(f"\nEvaluating {name}...")
        y_pred = model.predict(X_test)
        
        y_prob = None
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_test)
            
        metrics = get_metrics(y_test, y_pred, y_prob)
        metrics['Model'] = name
        results.append(metrics)
        
        # Print Confusion Matrix
        print(f"Confusion Matrix:\n{metrics['Confusion Matrix']}")
        
        # Generate ROC Curve
        plot_roc_curve(y_test, y_prob, name, n_classes)

        # Track best
        current_score = metrics[primary_metric]
        if isinstance(current_score, (int, float)) and current_score > best_score:
            best_score = current_score
            best_model_name = name

    # Comparison Table
    results_df = pd.DataFrame(results)
    
    # Reorder columns
    cols = ['Model', 'Accuracy', 'Precision', 'Recall', 'F1 Score', 'ROC-AUC']
    results_df = results_df[cols]
    
    print("\n" + "="*50)
    print("FINAL COMPARISON TABLE")
    print("="*50)
    print(results_df.to_string(index=False))
    print("="*50)
    
    # Identify Best Models
    individual_models = [m for m in results if 'Ensemble' not in m['Model']]
    ensemble_models = [m for m in results if 'Ensemble' in m['Model']]
    
    best_ind = max(individual_models, key=lambda x: x['ROC-AUC']) if individual_models else None
    best_ens = max(ensemble_models, key=lambda x: x['ROC-AUC']) if ensemble_models else None
    
    print("\n--- Summary ---")
    if best_ind:
        print(f"Best Individual Model: {best_ind['Model']} (AUC: {best_ind['ROC-AUC']:.4f}, F1: {best_ind['F1 Score']:.4f})")
    if best_ens:
        print(f"Best Ensemble Model:   {best_ens['Model']} (AUC: {best_ens['ROC-AUC']:.4f}, F1: {best_ens['F1 Score']:.4f})")
        
    print(f"Overall Best Model:      {best_model_name} (AUC: {best_score:.4f})")
    
    print("\n--- Recommendation ---")
    print(f"Recommendation: Select {best_model_name} for deployment.")
    print(f"Reason: It achieved the highest ROC-AUC ({best_score:.4f}), indicating superior capability in distinguishing between credit risk classes.")

if __name__ == "__main__":
    main()
