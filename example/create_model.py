"""
Create a new Iris model and save it to the models directory
"""
import os
import pickle
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Set paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(CURRENT_DIR, 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'iris_model.pkl')

# Create models directory if it doesn't exist
os.makedirs(MODEL_DIR, exist_ok=True)

# Load iris dataset
print("Loading Iris dataset...")
iris = load_iris()
X = iris.data
y = iris.target

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a simple RandomForest classifier
print("Training model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"Model accuracy: {accuracy:.4f}")

# Save the model
print(f"Saving model to {MODEL_PATH}...")
with open(MODEL_PATH, 'wb') as f:
    pickle.dump(model, f)

print("Model created and saved successfully!")