from typing import Any, Dict, List, Optional
import json

class PredictionRequestBuilder:
    """Builds prediction requests for ML services."""
    
    @staticmethod
    def format_features(features: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format feature values according to a schema.
        
        Args:
            features: Raw feature values
            schema: Optional schema defining feature types
            
        Returns:
            Formatted feature values
        """
        if not schema:
            return features
            
        result = {}
        schema_properties = schema.get("properties", {})
        
        for feature_name, value in features.items():
            # Skip if feature not in schema
            if feature_name not in schema_properties:
                continue
                
            feature_schema = schema_properties[feature_name]
            feature_type = feature_schema.get("type")
            
            # Convert value to the correct type
            if feature_type == "integer" and value is not None:
                result[feature_name] = int(value)
            elif feature_type == "number" and value is not None:
                result[feature_name] = float(value)
            elif feature_type == "boolean" and value is not None:
                result[feature_name] = bool(value)
            elif feature_type == "string" and value is not None:
                result[feature_name] = str(value)
            elif feature_type == "array" and value is not None:
                if isinstance(value, list):
                    result[feature_name] = value
                elif isinstance(value, str):
                    # Try to parse as JSON
                    try:
                        result[feature_name] = json.loads(value)
                    except json.JSONDecodeError:
                        result[feature_name] = [value]
                else:
                    result[feature_name] = [value]
            else:
                result[feature_name] = value
        
        return result
    
    @staticmethod
    def build_batch_prediction_request(instances: List[Dict[str, Any]], model_id: str) -> Dict[str, Any]:
        """Build a batch prediction request.
        
        Args:
            instances: List of feature dictionaries
            model_id: The model identifier
            
        Returns:
            Batch prediction request
        """
        return {
            "model_id": model_id,
            "instances": instances
        }
    
    @staticmethod
    def extract_prediction_results(response: Dict[str, Any], prediction_key: str = "predictions") -> List[Any]:
        """Extract prediction results from a response.
        
        Args:
            response: Prediction response
            prediction_key: Key for predictions in the response
            
        Returns:
            List of prediction results
        """
        if not response or prediction_key not in response:
            return []
            
        predictions = response[prediction_key]
        
        if not isinstance(predictions, list):
            return [predictions]
            
        return predictions
