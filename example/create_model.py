#!/usr/bin/env python3
"""
Create and save the Iris classifier model
"""
import os
import pickle
import numpy as np
from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Set up paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'iris_model.pkl')

def create_and_save_model():
    """Create and save the iris classifier model"""
    print("Loading Iris dataset...")
    iris = datasets.load_iris()
    X = iris.data
    y = iris.target
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create and train the model
    print("Training Random Forest classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model accuracy: {accuracy:.4f}")
    
    # Create the models directory if it doesn't exist
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Save the model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model saved to {MODEL_PATH}")
    
    # Optional: Show feature importances
    feature_names = iris.feature_names
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("\nFeature ranking:")
    for i, idx in enumerate(indices):
        print(f"{i+1}. {feature_names[idx]} ({importances[idx]:.4f})")

if __name__ == "__main__":
    create_and_save_model()