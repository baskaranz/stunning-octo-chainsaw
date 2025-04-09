"""
Iris Model Server - Simple Flask API to serve the sklearn Iris model
"""
import os
import pickle
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load the model
MODEL_PATH = os.environ.get('MODEL_PATH', 'models/iris_model.pkl')

def load_model(model_path):
    """Load the iris model from the specified path"""
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        print(f"Model loaded successfully from {model_path}")
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None

# Feature names expected by the model
FEATURE_NAMES = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']

# Class names for the iris dataset
CLASS_NAMES = ['setosa', 'versicolor', 'virginica']

# Global model variable
model = load_model(MODEL_PATH)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    if model is not None:
        return jsonify({"status": "healthy", "model": "iris"}), 200
    return jsonify({"status": "unhealthy", "error": "Model not loaded"}), 500

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint for making predictions with the iris model"""
    try:
        # Get request data
        data = request.get_json()
        features = data.get('features', {})
        
        # Log input for debugging
        print(f"Received prediction request with features: {features}")
        
        # Extract features in the correct order
        feature_values = []
        for feature in FEATURE_NAMES:
            value = features.get(feature)
            if value is None:
                return jsonify({
                    "error": f"Missing feature: {feature}",
                    "required_features": FEATURE_NAMES
                }), 400
            feature_values.append(float(value))
        
        # Make prediction
        features_array = np.array([feature_values])
        class_idx = int(model.predict(features_array)[0])
        probabilities = model.predict_proba(features_array)[0].tolist()
        
        class_name = CLASS_NAMES[class_idx]
        
        # Create the response
        response = {
            "prediction": {
                "class_index": class_idx,
                "class_name": class_name,
                "probabilities": {
                    CLASS_NAMES[i]: float(prob) for i, prob in enumerate(probabilities)
                }
            },
            "features_received": features
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Error making prediction: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Start the server
    app.run(host='0.0.0.0', port=port, debug=True)