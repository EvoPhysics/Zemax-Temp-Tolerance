"""
07_Model_Prediction.py - Task C: Model Inference

Task:
1. Load the dataset and retrain the model (since we didn't save the pickle).
2. Predict RMS Spot Radius for a specific user input (e.g., 73.5C).
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

def main():
    print("=" * 60)
    print("Task C: AI Prediction Inference")
    print("=" * 60)
    
    # 1. Load Data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "models", "dataset_v1.csv")
    
    if not os.path.exists(csv_file):
        print(f"ERROR: Dataset {csv_file} not found.")
        return

    df = pd.read_csv(csv_file)
    X = df[['Temperature']].values
    y = df['Spot_Radius'].values
    
    # 2. Train Model (Quick Retrain)
    degree = 2
    poly = PolynomialFeatures(degree=degree)
    X_poly = poly.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_poly, y)
    
    # 3. Predict
    target_temp = 73.5
    X_target = np.array([[target_temp]])
    X_target_poly = poly.transform(X_target)
    
    predicted_spot = model.predict(X_target_poly)[0]
    
    print("-" * 40)
    print(f"Input Temperature: {target_temp} C")
    print(f"Predicted RMS Spot: {predicted_spot:.4f} microns")
    print("-" * 40)
    print("Note: This prediction is based on the Polynomial Regression (Deg=2)")
    print("      trained on 200 samples from dataset_v1.csv.")

if __name__ == "__main__":
    main()
