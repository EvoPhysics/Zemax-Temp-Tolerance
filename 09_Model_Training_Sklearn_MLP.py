
"""
09_Model_Training_Sklearn_MLP.py - Neural Network Training for Optical Tolerance Analysis (Sklearn Version)

Task:
1. Load 'dataset_v2_tolerance.csv'.
2. Preprocess: Split 80/20, Scale Inputs (StandardScaler).
3. Train a Sklearn MLPRegressor to predict RMS Spot Radius.
4. Evaluate with R2 Score.
5. Save Model (.pkl) and Scaler (.pkl).
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import r2_score, mean_squared_error
import joblib
import os
import sys

# --- Configuration ---
SEED = 42
EPOCHS = 1000 # Max iter
DATA_PATH = os.path.join("models", "dataset_v2_tolerance.csv")
MODEL_SAVE_PATH = os.path.join("models", "optical_mlp_sklearn.pkl")
SCALER_SAVE_PATH = os.path.join("models", "input_scaler.pkl")

# Set random seeds for reproducibility
np.random.seed(SEED)

def main():
    print("=" * 60)
    print("Sklearn MLP Training: Optical Tolerance Analysis")
    print("=" * 60)

    # --- Step 1: Data Loading & Preprocessing ---
    if not os.path.exists(DATA_PATH):
        print(f"Error: Dataset not found at {DATA_PATH}")
        return

    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # Check for NaN and drop (robustness)
    if df.isnull().values.any():
        print(f"Warning: Found {df.isnull().sum().sum()} missing values. Dropping rows...")
        df = df.dropna()

    # Features (X) and Label (y)
    # X: Temp (1) + 3 Lenses * 4 Tols = 13 Columns
    X_raw = df.iloc[:, :-1].values
    y_raw = df.iloc[:, -1].values

    print(f"Dataset Shape: {X_raw.shape}")

    # Split Data
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y_raw, test_size=0.2, random_state=SEED
    )

    # Scale Inputs
    print("Scaling features...")
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_test = scaler.transform(X_test_raw)

    # --- Step 2: Model Initialization & Training ---
    print(f"\nInitializing MLP Regressor...")
    # Architecture similar to PyTorch: 13 -> 64 -> 64 -> 1
    model = MLPRegressor(
        hidden_layer_sizes=(64, 64),
        activation='relu',
        solver='adam',
        alpha=0.0001,
        batch_size='auto',
        learning_rate='constant',
        learning_rate_init=0.001,
        max_iter=EPOCHS,
        random_state=SEED,
        verbose=True,
        early_stopping=True,
        validation_fraction=0.1
    )

    print("Training model...")
    model.fit(X_train, y_train)

    # --- Step 3: Evaluation ---
    print("\nEvaluating on Test Set...")
    y_pred = model.predict(X_test)
    
    test_mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("-" * 30)
    print(f"Test MSE: {test_mse:.4f}")
    print(f"Test R2 Score: {r2:.4f}")
    print("-" * 30)

    if r2 > 0.85:
        print("✅ Success! R2 Score > 0.85")
    else:
        print("⚠️ Warning: R2 Score below target. Consider more data or tuning.")

    # --- Step 4: Save Artifacts ---
    print("\nSaving artifacts...")
    joblib.dump(model, MODEL_SAVE_PATH)
    joblib.dump(scaler, SCALER_SAVE_PATH)
    
    print(f"Model saved to: {MODEL_SAVE_PATH}")
    print(f"Scaler saved to: {SCALER_SAVE_PATH}")

if __name__ == "__main__":
    main()
