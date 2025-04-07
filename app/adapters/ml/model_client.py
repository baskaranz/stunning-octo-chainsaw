from typing import Any, Dict, List, Optional
from fastapi import Depends
import json

from app.adapters.api.http_client import HttpClient
from app.config.data_source_config_manager import DataSourceConfigManager
from app.common.errors.custom_exceptions import ModelError
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ModelClient:
    """Client for ML model inference services."""
    
    def __init__(
        self, 
        config_manager: DataSourceConfigManager = Depends(),
        http_client: HttpClient = Depends()
    ):
        self.config_manager = config_manager
        self.http_client = http_client
    
    async def predict(self, model_id: str, features: Dict[str, Any], source_id: str = "default") -> Dict[str, Any]:
        """Get predictions from an ML model.
        
        Args:
            model_id: The model identifier
            features: Model input features
            source_id: The ML service source ID
            
        Returns:
            Prediction results
        """
        # Get the ML service configuration
        config = self.config_manager.get_data_source_config("ml", source_id)
        if not config:
            raise ModelError(f"ML service configuration not found for source '{source_id}'", source_id)
        
        # Find the model endpoint
        models = config.get("models", {})
        model_config = models.get(model_id)
        if not model_config:
            raise ModelError(f"Model '{model_id}' not found in ML service '{source_id}'", source_id)
        
        endpoint = model_config.get("endpoint")
        if not endpoint:
            raise ModelError(f"Endpoint not defined for model '{model_id}' in ML service '{source_id}'", source_id)
        
        # Prepare request data - simpler format for the loan prediction example
        request_data = {
            "features": features
        }
        
        try:
            logger.info(f"Making prediction request for model '{model_id}' in source '{source_id}'")
            
            # Send prediction request
            response = await self.http_client.post(
                endpoint,
                data=request_data,
                source_id=source_id
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error making prediction with model '{model_id}' in source '{source_id}': {str(e)}")
            raise ModelError(f"Failed to get prediction: {str(e)}", source_id)
    
    # Additional domain-specific methods can be added through extension mechanisms
    # For example, the generic orchestrator example uses ml_extensions.py
