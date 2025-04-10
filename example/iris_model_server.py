"""
Iris Model Server - Simple Flask API to serve a basic Iris model
"""
import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Simple rule-based classification instead of using a pickled model
def rule_based_predict(features):
    """
    Simple rule-based prediction based on known Iris characteristics:
    - Setosa has small petals (length < 2.5)
    - Virginica has wide petals (width > 1.8)
    - Versicolor is in between
    """
    petal_length = features.get('petal_length', 0)
    petal_width = features.get('petal_width', 0)
    
    # Simple decision rules
    if petal_length < 2.5:
        class_idx = 0  # setosa
    elif petal_width > 1.8:
        class_idx = 2  # virginica
    else:
        class_idx = 1  # versicolor
    
    # Create probability distribution (simple mock)
    probabilities = [0.0, 0.0, 0.0]
    probabilities[class_idx] = 0.9  # 90% confidence in prediction
    
    # Distribute remaining probability to other classes
    for i in range(3):
        if i != class_idx:
            probabilities[i] = 0.05  # 5% to each other class
    
    return class_idx, probabilities

# Feature names expected by the model
FEATURE_NAMES = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']

# Class names for the iris dataset
CLASS_NAMES = ['setosa', 'versicolor', 'virginica']

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model": "iris"}), 200

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
        feature_values = {}
        for feature in FEATURE_NAMES:
            value = features.get(feature)
            if value is None:
                return jsonify({
                    "error": f"Missing feature: {feature}",
                    "required_features": FEATURE_NAMES
                }), 400
            feature_values[feature] = float(value)
        
        # Make prediction using rule-based system
        class_idx, probabilities = rule_based_predict(feature_values)
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