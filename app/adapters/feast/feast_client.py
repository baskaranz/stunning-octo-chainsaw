from typing import Any, Dict, List, Optional
from fastapi import Depends
from datetime import datetime
import importlib

from app.config.data_source_config_manager import DataSourceConfigManager
from app.common.errors.custom_exceptions import FeastError
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class FeastClient:
    """Client for Feast feature store operations."""
    
    def __init__(self, config_manager: DataSourceConfigManager = Depends()):
        self.config_manager = config_manager
        self.feature_stores = {}
        
        # Check if Feast is installed
        try:
            self.feast = importlib.import_module("feast")
            logger.info("Feast module loaded successfully")
        except ImportError:
            logger.warning("Feast module not found. Feature store operations will not be available.")
            self.feast = None
    
    def _get_feature_store(self, source_id: str = "default"):
        """Get a Feast feature store for the specified source ID."""
        if self.feast is None:
            raise FeastError("Feast module not available", source_id)
            
        if source_id in self.feature_stores:
            return self.feature_stores[source_id]
        
        # Get the Feast configuration
        config = self.config_manager.get_data_source_config("feast", source_id)
        if not config:
            raise FeastError(f"Feast configuration not found for source '{source_id}'", source_id)
        
        # Create the feature store
        try:
            repo_path = config.get("repo_path")
            if not repo_path:
                raise FeastError(f"Missing repo path for Feast source '{source_id}'", source_id)
            
            feature_store = self.feast.FeatureStore(repo_path=repo_path)
            self.feature_stores[source_id] = feature_store
            return feature_store
        except Exception as e:
            logger.error(f"Error creating Feast feature store for source '{source_id}': {str(e)}")
            raise FeastError(f"Error initializing Feast feature store: {str(e)}", source_id)
    
    async def get_online_features(self, entity_rows: List[Dict[str, Any]], feature_refs: List[str], 
                                source_id: str = "default") -> Dict[str, List[Any]]:
        """Get online features from the feature store.
        
        Args:
            entity_rows: List of entity dictionaries
            feature_refs: List of feature references
            source_id: The feature store source ID
            
        Returns:
            Dictionary mapping feature names to feature values
        """
        if self.feast is None:
            raise FeastError("Feast module not available", source_id)
            
        feature_store = self._get_feature_store(source_id)
        
        try:
            logger.info(f"Retrieving features {feature_refs} for {len(entity_rows)} entities from source '{source_id}'")
            features = feature_store.get_online_features(
                entity_rows=entity_rows,
                features=feature_refs
            )
            
            # Convert Feast response to dictionary
            result = {}
            for feature_name in features.keys():
                result[feature_name] = features[feature_name]
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving features from source '{source_id}': {str(e)}")
            raise FeastError(f"Failed to retrieve features: {str(e)}", source_id)
    
    # Example operations for the customer domain
    
    async def get_customer_features(self, customer_id: str, feature_refs: Optional[List[str]] = None, 
                                  source_id: str = "default") -> Dict[str, Any]:
        """Get features for a specific customer.
        
        Args:
            customer_id: The customer ID
            feature_refs: List of feature references (or None for default set)
            source_id: The feature store source ID
            
        Returns:
            Dictionary of feature values
        """
        # Get default feature references if not provided
        if feature_refs is None:
            # Get from configuration
            config = self.config_manager.get_data_source_config("feast", source_id)
            default_features = config.get("default_customer_features", [])
            feature_refs = default_features
        
        # Create entity row
        entity_row = {"customer_id": customer_id}
        
        try:
            features_result = await self.get_online_features(
                entity_rows=[entity_row],
                feature_refs=feature_refs,
                source_id=source_id
            )
            
            # Convert to a simpler format with a single value per feature
            result = {}
            for feature_name, values in features_result.items():
                if values and len(values) > 0:
                    result[feature_name] = values[0]
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving features for customer {customer_id}: {str(e)}")
            raise FeastError(f"Failed to retrieve customer features: {str(e)}", source_id)
