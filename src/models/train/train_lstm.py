import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from project.src.data_loader import load_transaction_data, load_feature_store
except ImportError:
    try:
        from data_loader import load_transaction_data, load_feature_store
    except ImportError:
         sys.path.append(os.path.dirname(os.path.abspath(__file__)))
         from data_loader import load_transaction_data, load_feature_store

def prepare_sequences(txn_df, feat_df, seq_length=10, max_customers=5000):
    print("Preparing sequences for LSTM...")
    
    # Ensure date format
    txn_df['transaction_date'] = pd.to_datetime(txn_df['transaction_date'])
    
    # Scale numerical features (amount)
    scaler = StandardScaler()
    txn_df['amount_scaled'] = scaler.fit_transform(txn_df[['amount_inr']].fillna(0))
    
    # Sort by customer and date
    txn_df = txn_df.sort_values(['customer_id', 'transaction_date'])
    
    # Get target mapping
    if 'risk_band' in feat_df.columns:
        risk_map = {'Low': 0, 'Moderate': 1, 'Medium': 1, 'High': 2, 'Very High': 3}
        # Filter rows where risk_band is not null/valid
        feat_df = feat_df[feat_df['risk_band'].isin(risk_map.keys())].copy()
        feat_df['target'] = feat_df['risk_band'].map(risk_map)
    else:
        print("Warning: 'risk_band' not found in feature store.")
        return np.array([]), np.array([])
    
    # Create dictionary for fast lookup
    target_dict = feat_df.set_index('customer_id')['target'].to_dict()
    
    # Group by customer
    grouped = txn_df.groupby('customer_id')
    
    sequences = []
    targets = []
    
    count = 0
    print(f"Processing up to {max_customers} customers...")
    
    for customer_id, group in grouped:
        if customer_id not in target_dict:
            continue
            
        target = target_dict[customer_id]
        
        # Get sequence of scaled amounts
        seq = group['amount_scaled'].values
        
        # Pad or truncate
        if len(seq) < seq_length:
            # Pad with zeros at the beginning (pre-padding is generally better for LSTMs)
            seq = np.pad(seq, (seq_length - len(seq), 0), 'constant')
        else:
            # Take last N transactions (most recent)
            seq = seq[-seq_length:]
            
        sequences.append(seq)
        targets.append(target)
        
        count += 1
        if count >= max_customers:
            break
            
    if not sequences:
        return np.array([]), np.array([])
        
    X = np.array(sequences)
    # Reshape for LSTM: (samples, time_steps, features)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    y = np.array(targets)
    
    return X, y

def build_lstm_model(input_shape, num_classes):
    print("Building LSTM model...")
    model = Sequential()
    # LSTM layer
    model.add(LSTM(64, input_shape=input_shape, return_sequences=False))
    model.add(Dropout(0.2))
    # Dense layers
    model.add(Dense(32, activation='relu'))
    model.add(Dense(num_classes, activation='softmax')) # Classification
    
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

def main():
    try:
        print("Loading data...")
        txn_df = load_transaction_data()
        feat_df = load_feature_store()
        
        seq_length = 20
        # Convert max_customers to int just in case
        X, y = prepare_sequences(txn_df, feat_df, seq_length=seq_length, max_customers=5000)
        
        if X.size == 0:
            print("Error: No data sequences created. Check data availability and memory.")
            return

        print(f"Data prepared: X shape {X.shape}, y shape {y.shape}")
        
        # Check unique classes
        unique_classes = np.unique(y)
        print(f"Target classes: {unique_classes}")
        
        if len(unique_classes) < 2:
            print("Error: Not enough classes in target variable for classification.")
            return

        # Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Build model
        num_classes = len(unique_classes)
        # Use simple mapping: 0 to num_classes-1 if targets are not contiguous
        # But our map is 0,1,2,3 so it's fine if all present. If some missing, might need relabeling.
        
        model = build_lstm_model((seq_length, 1), 4) # Hardcode 4 classes (Low, Moderate/Medium, High, Very High) if necessary
        
        # Train
        print("Training LSTM...")
        history = model.fit(X_train, y_train, epochs=5, batch_size=32, validation_split=0.1, verbose=1)
        
        # Evaluate
        print("\nEvaluating LSTM...")
        loss, acc = model.evaluate(X_test, y_test, verbose=0)
        print(f"Test Accuracy: {acc:.4f}")
        
        # Save model
        model_path = os.path.join(project_root, 'project', 'lstm_model.keras')
        model.save(model_path)
        print(f"Model saved to {model_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
