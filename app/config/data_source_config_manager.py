from typing import Any, Dict, List, Optional
from fastapi import Depends

from app.config.config_loader import ConfigLoader
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class DataSourceConfigManager:
    """Manages data source configurations for the orchestration engine."""
    
    def __init__(self, config_loader: ConfigLoader = Depends()):
        self.config_loader = config_loader
        self.source_cache = {}
    
    def get_data_source_config(self, source_type: str, source_id: str) -> Optional[Dict[str, Any]]:
        """Get the configuration for a specific data source.
        
        Args:
            source_type: The type of data source (e.g., "database", "api")
            source_id: The identifier for the specific source
            
        Returns:
            The data source configuration or None if not found
        """
        # Check cache first
        cache_key = f"{source_type}.{source_id}"
        if cache_key in self.source_cache:
            return self.source_cache[cache_key]
        
        # Load integration configuration based on source type
        if source_type == "database":
            config_file = "database.yaml"
        elif source_type == "api":
            config_file = "integrations/api_sources.yaml"
        elif source_type == "feast":
            config_file = "integrations/feast_config.yaml"
        else:
            config_file = f"integrations/{source_type}.yaml"
        
        config = self.config_loader.load_yaml_file(config_file)
        if not config:
            logger.warning(f"No configuration found for source type '{source_type}'")
            return None
        
        # Get the configuration for this specific source
        sources = config.get("sources", {})
        source_config = sources.get(source_id)
        
        if not source_config:
            logger.warning(f"No configuration found for source '{source_id}' of type '{source_type}'")
            return None
        
        # Cache the result
        self.source_cache[cache_key] = source_config
        return source_config
    
    def get_all_data_sources(self, source_type: str) -> Dict[str, Any]:
        """Get all data source configurations for a type.
        
        Args:
            source_type: The type of data source
            
        Returns:
            A dictionary mapping source IDs to source configurations
        """
        if source_type == "database":
            config_file = "database.yaml"
        elif source_type == "api":
            config_file = "integrations/api_sources.yaml"
        elif source_type == "feast":
            config_file = "integrations/feast_config.yaml"
        else:
            config_file = f"integrations/{source_type}.yaml"
        
        config = self.config_loader.load_yaml_file(config_file)
        return config.get("sources", {})
    
    def reload_data_source_config(self, source_type: Optional[str] = None) -> None:
        """Reload data source configurations from disk.
        
        Args:
            source_type: If provided, only reload this specific source type
        """
        if source_type:
            # Clear cache entries for this source type
            for cache_key in list(self.source_cache.keys()):
                if cache_key.startswith(f"{source_type}."):
                    del self.source_cache[cache_key]
            
            # Reload the source type configuration
            if source_type == "database":
                self.config_loader.reload_config("database.yaml")
            elif source_type == "api":
                self.config_loader.reload_config("integrations/api_sources.yaml")
            elif source_type == "feast":
                self.config_loader.reload_config("integrations/feast_config.yaml")
            else:
                self.config_loader.reload_config(f"integrations/{source_type}.yaml")
        else:
            # Clear all cache entries
            self.source_cache.clear()
            
            # Reload all configurations
            self.config_loader.reload_config()
        
        logger.info(f"Reloaded data source configurations {'for type ' + source_type if source_type else 'for all types'}")
