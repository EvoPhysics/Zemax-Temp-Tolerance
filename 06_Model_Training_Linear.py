"""
20_Model_Training_Linear.py - Task B: First Training

Task:
1. Load 'dataset_v1.csv'
2. Train a Polynomial Regression Model (Degree 2) to predict Spot Radius from Temperature.
3. Evaluate using 80/20 train/test split.
4. Output R2 Score.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

def main():
    print("=" * 60)
    print("Task B: First AI Training (Polynomial Regression)")
    print("=" * 60)
    
    # 1. Load Data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "models", "dataset_v1.csv")
    if not os.path.exists(csv_file):
        print(f"ERROR: Dataset {csv_file} not found. Run Task A first.")
        return

    print(f"Loading {csv_file}...")
    df = pd.read_csv(csv_file)
    
    X = df[['Temperature']].values
    y = df['Spot_Radius'].values
    
    print(f"Loaded {len(df)} samples.")
    
    # 2. Split Data (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples:  {len(X_test)}")
    
    # 3. Polynomial Features (Degree 2)
    # Why Degree 2? Thermal defocus is typically parabolic (quadratic) around the minimum.
    degree = 2
    poly = PolynomialFeatures(degree=degree)
    X_train_poly = poly.fit_transform(X_train)
    X_test_poly = poly.transform(X_test)
    
    # 4. Train Linear Regression on Polynomial Features
    model = LinearRegression()
    model.fit(X_train_poly, y_train)
    
    # 5. Prediction & Evaluation
    y_pred_train = model.predict(X_train_poly)
    y_pred_test = model.predict(X_test_poly)
    
    r2_train = r2_score(y_train, y_pred_train)
    r2_test = r2_score(y_test, y_pred_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    print("-" * 40)
    print("MODEL PERFORMANCE")
    print("-" * 40)
    print(f"Polynomial Degree: {degree}")
    print(f"R2 Score (Train):  {r2_train:.4f}")
    print(f"R2 Score (Test):   {r2_test:.4f}")
    print(f"RMSE (Test):       {rmse:.4f} microns")
    print("-" * 40)
    
    # 6. Visualization (Optional but helpful)
    # Generate a smooth curve for plotting
    X_range = np.linspace(X.min(), X.max(), 100).reshape(-1, 1)
    X_range_poly = poly.transform(X_range)
    y_range_pred = model.predict(X_range_poly)
    
    plt.figure(figsize=(10, 6))
    plt.scatter(X_train, y_train, color='blue', alpha=0.5, label='Training Data')
    plt.scatter(X_test, y_test, color='green', alpha=0.5, label='Test Data')
    plt.plot(X_range, y_range_pred, color='red', linewidth=2, label=f'Poly Fit (Deg {degree})')
    
    plt.title(f"Thermal Spot Analysis (R2={r2_test:.4f})")
    plt.xlabel("Temperature (C)")
    plt.ylabel("RMS Spot Radius (microns)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_file = "model_v1_fit.png"
    plt.savefig(plot_file)
    print(f"Plot saved to {plot_file}")
    
    # 7. Validation
    if r2_test > 0.9:
        print("\n✅ SUCCESS: R2 Score > 0.9. The model captures the physics well.")
    else:
        print("\n❌ FAILURE: R2 Score too low. Check data or model complexity.")

if __name__ == "__main__":
    import os
    main()
