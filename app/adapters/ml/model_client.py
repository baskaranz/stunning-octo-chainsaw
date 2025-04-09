from typing import Any, Dict, List, Optional
from fastapi import Depends
import json
import asyncio

from app.adapters.api.http_client import HttpClient
from app.config.data_source_config_manager import DataSourceConfigManager
from app.common.errors.custom_exceptions import ModelError
from app.common.utils.logging_utils import get_logger
from app.adapters.ml.model_loader import ModelLoader

logger = get_logger(__name__)

class ModelClient:
    """Client for ML model inference services."""
    
    def __init__(
        self, 
        config_manager: DataSourceConfigManager = Depends(),
        http_client: HttpClient = Depends(),
        model_loader: Optional[ModelLoader] = None
    ):
        self.config_manager = config_manager
        self.http_client = http_client
        self.model_loader = model_loader or ModelLoader()
        self._model_locks = {}  # Dict to store locks for each model
    
    def _get_model_lock(self, model_key: str):
        """Get or create a lock for a specific model."""
        if model_key not in self._model_locks:
            self._model_locks[model_key] = asyncio.Lock()
        return self._model_locks[model_key]
    
    async def predict(self, model_id: str, features: Dict[str, Any], source_id: str = "default", domain: Optional[str] = None) -> Dict[str, Any]:
        """Get predictions from an ML model.
        
        Args:
            model_id: The model identifier
            features: Model input features
            source_id: The ML service source ID
            domain: Optional domain for domain-specific configurations
            
        Returns:
            Prediction results
        """
        # Get the ML service configuration
        config = self.config_manager.get_data_source_config("ml", source_id, domain)
        if not config:
            raise ModelError(f"ML service configuration not found for source '{source_id}'", source_id)
        
        # Find the model configuration
        models = config.get("models", {})
        model_config = models.get(model_id)
        if not model_config:
            raise ModelError(f"Model '{model_id}' not found in ML service '{source_id}'", source_id)
        
        # Create a unique key for this model
        model_key = f"{source_id}_{model_id}"
        
        # Get or create a lock for this model to prevent concurrent loading
        async with self._get_model_lock(model_key):
            # Check if model needs to be loaded
            if "source" in model_config and model_config.get("source", {}).get("type") != "http":
                # Load the model if it has a source configuration
                try:
                    # This will return either the cached config or newly loaded config
                    model_config = await self.model_loader.load_model(model_config, source_id)
                except Exception as e:
                    logger.error(f"Error loading model '{model_id}' from source '{source_id}': {str(e)}")
                    raise ModelError(f"Failed to load model: {str(e)}", source_id)
        
        endpoint = model_config.get("endpoint")
        if not endpoint:
            raise ModelError(f"Endpoint not defined for model '{model_id}' in ML service '{source_id}'", source_id)
        
        # Prepare request data
        request_data = {
            "features": features
        }
        
        try:
            logger.info(f"Making prediction request for model '{model_id}' in source '{source_id}'")
            
            # Get headers from model config
            headers = model_config.get("headers", {})
            
            # Send prediction request
            if endpoint.startswith(('http://', 'https://')):
                # For dynamically generated endpoints (from model loader)
                response = await self.http_client.post(
                    endpoint,
                    data=request_data,
                    headers=headers,
                    direct_url=True
                )
            else:
                # For configured endpoints in the service
                response = await self.http_client.post(
                    endpoint,
                    data=request_data,
                    source_id=source_id,
                    domain=domain
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error making prediction with model '{model_id}' in source '{source_id}': {str(e)}")
            raise ModelError(f"Failed to get prediction: {str(e)}", source_id)
    
    async def shutdown(self):
        """Clean up resources when shutting down."""
        if self.model_loader:
            await self.model_loader.unload_all_models()
    
    # Additional domain-specific methods can be added through extension mechanisms
    # For example, the generic orchestrator example uses ml_extensions.py