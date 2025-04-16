from typing import Any, Dict, List, Optional
from fastapi import Depends
import importlib

from app.config.data_source_config_manager import DataSourceConfigManager
from app.common.errors.custom_exceptions import FeastError
from app.common.utils.logging_utils import get_logger
from app.adapters.database.database_client import DatabaseClient

logger = get_logger(__name__)

class FeastClient:
    """Client for Feast feature store operations."""
    
    def __init__(
        self, 
        config_manager: DataSourceConfigManager = Depends(),
        database_client: Optional[DatabaseClient] = Depends()
    ):
        self.config_manager = config_manager
        self.database_client = database_client
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
    
    async def get_online_features(
        self, 
        entity_rows: List[Dict[str, Any]], 
        feature_refs: List[str], 
        source_id: str = "default",
        domain: Optional[str] = None, 
        use_fallback: bool = True
    ) -> Dict[str, List[Any]]:
        """Get online features from the feature store.
        
        Args:
            entity_rows: List of entity dictionaries
            feature_refs: List of feature references
            source_id: The feature store source ID
            domain: Optional domain for domain-specific configurations
            use_fallback: Whether to use database fallback if Feast fails
            
        Returns:
            Dictionary mapping feature names to feature values
        """
        if self.feast is None:
            if use_fallback and self.database_client:
                return await self._get_features_from_database(
                    entity_rows, feature_refs, source_id, domain
                )
            raise FeastError("Feast module not available", source_id)
            
        try:
            feature_store = self._get_feature_store(source_id)
            
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
            
            # Try database fallback if enabled
            if use_fallback and self.database_client:
                logger.info(f"Using database fallback for features in source '{source_id}'")
                try:
                    return await self._get_features_from_database(
                        entity_rows, feature_refs, source_id, domain
                    )
                except Exception as fallback_error:
                    logger.error(f"Database fallback also failed: {str(fallback_error)}")
            
            # If no fallback or fallback failed
            raise FeastError(f"Failed to retrieve features: {str(e)}", source_id)
    
    async def _get_features_from_database(
        self, 
        entity_rows: List[Dict[str, Any]], 
        feature_refs: List[str], 
        source_id: str = "default",
        domain: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        """Fallback method to get features from the database instead of Feast."""
        if not self.database_client:
            raise FeastError("Database client not available for fallback", source_id)
        
        # Get the Feast configuration
        config = self.config_manager.get_data_source_config("feast", source_id, domain)
        if not config:
            raise FeastError(f"Feast configuration not found for source '{source_id}'", source_id)
        
        # Check if database fallback is enabled and configured
        fallback_config = config.get("database_fallback", {})
        if not fallback_config.get("enabled", False):
            raise FeastError(f"Database fallback not enabled for source '{source_id}'", source_id)
        
        # Get table and mapping from config
        table = fallback_config.get("table")
        entity_key = fallback_config.get("entity_key")
        mapping = fallback_config.get("mapping", {})
        
        if not table or not entity_key or not mapping:
            raise FeastError(f"Incomplete database fallback configuration for source '{source_id}'", source_id)
        
        # Collect entity IDs from entity rows
        entity_ids = []
        for row in entity_rows:
            for key, value in row.items():
                if key == entity_key:
                    entity_ids.append(value)
                    break
        
        if not entity_ids:
            raise FeastError(f"No entity IDs found in entity rows for key '{entity_key}'", source_id)
        
        # Build columns to select
        db_columns = ", ".join([mapping.get(ref, ref) for ref in feature_refs])
        
        # Create a query that uses the IN clause for multiple entity IDs
        placeholders = ", ".join([f":{entity_key}_{i}" for i in range(len(entity_ids))])
        query = f"SELECT {entity_key}, {db_columns} FROM {table} WHERE {entity_key} IN ({placeholders})"
        
        # Create parameters dictionary with named placeholders
        params = {f"{entity_key}_{i}": entity_id for i, entity_id in enumerate(entity_ids)}
        
        # Execute the query with all entity IDs in a single call
        rows = await self.database_client.query(query, params)
        
        # Build result dictionary in the same format as Feast
        result = {feature_ref: [] for feature_ref in feature_refs}
        
        # Create a mapping from entity ID to result row
        entity_to_row = {str(row[entity_key]): row for row in rows}
        
        # Fill in values for each entity in the same order as entity_rows
        for row in entity_rows:
            entity_id = None
            for key, value in row.items():
                if key == entity_key:
                    entity_id = str(value)
                    break
                    
            if entity_id and entity_id in entity_to_row:
                db_row = entity_to_row[entity_id]
                for feature_ref in feature_refs:
                    db_column = mapping.get(feature_ref, feature_ref)
                    if db_column in db_row:
                        result[feature_ref].append(db_row[db_column])
                    else:
                        result[feature_ref].append(None)
            else:
                # Entity not found in database, add None for all features
                for feature_ref in feature_refs:
                    result[feature_ref].append(None)
        
        return result
    
    # Example operations for the customer domain
    
    async def get_customer_features(
        self, 
        customer_id: str, 
        feature_refs: Optional[List[str]] = None, 
        source_id: str = "default",
        domain: Optional[str] = None,
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """Get features for a specific customer.
        
        Args:
            customer_id: The customer ID
            feature_refs: List of feature references (or None for default set)
            source_id: The feature store source ID
            domain: Optional domain for domain-specific configurations
            use_fallback: Whether to use database fallback if Feast fails
            
        Returns:
            Dictionary of feature values
        """
        # Get default feature references if not provided
        if feature_refs is None:
            # Get from configuration
            config = self.config_manager.get_data_source_config("feast", source_id, domain)
            default_features = config.get("default_customer_features", [])
            feature_refs = default_features
        
        # Create entity row
        entity_row = {"customer_id": customer_id}
        
        try:
            features_result = await self.get_online_features(
                entity_rows=[entity_row],
                feature_refs=feature_refs,
                source_id=source_id,
                domain=domain,
                use_fallback=use_fallback
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
            
    async def get_iris_features(
        self, 
        flower_id: int, 
        feature_refs: Optional[List[str]] = None, 
        source_id: str = "iris_features",
        domain: str = "iris_example",
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """Get features for a specific iris flower.
        
        Args:
            flower_id: The iris flower ID
            feature_refs: List of feature references (or None for default set)
            source_id: The feature store source ID
            domain: The domain for domain-specific configurations
            use_fallback: Whether to use database fallback if Feast fails
            
        Returns:
            Dictionary of feature values
        """
        # Get default feature references if not provided
        if feature_refs is None:
            # Get from configuration
            config = self.config_manager.get_data_source_config("feast", source_id, domain)
            default_features = config.get("default_iris_features", [])
            feature_refs = default_features
        
        # Create entity row
        entity_row = {"id": flower_id}
        
        try:
            features_result = await self.get_online_features(
                entity_rows=[entity_row],
                feature_refs=feature_refs,
                source_id=source_id,
                domain=domain,
                use_fallback=use_fallback
            )
            
            # Convert to a simpler format with a single value per feature
            result = {}
            for feature_name, values in features_result.items():
                if values and len(values) > 0:
                    result[feature_name] = values[0]
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving features for iris flower {flower_id}: {str(e)}")
            raise FeastError(f"Failed to retrieve iris features: {str(e)}", source_id)
