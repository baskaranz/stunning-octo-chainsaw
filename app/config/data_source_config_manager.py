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
    
    def get_data_source_config(self, source_type: str, source_id: str, domain: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the configuration for a specific data source.
        
        Args:
            source_type: The type of data source (e.g., "database", "api")
            source_id: The identifier for the specific source
            domain: Optional domain name to fetch domain-specific configs
            
        Returns:
            The data source configuration or None if not found
        """
        # Check cache first
        cache_key = f"{domain}.{source_type}.{source_id}" if domain else f"{source_type}.{source_id}"
        if cache_key in self.source_cache:
            return self.source_cache[cache_key]
        
        # Load configuration based on source type
        config = None
        if source_type == "database":
            config = self.config_loader.load_database_config(domain)
        elif source_type == "api":
            config = self.config_loader.load_integration_config("api_sources", domain)
        elif source_type == "feast":
            config = self.config_loader.load_integration_config("feast_config", domain)
        elif source_type == "ml":
            config = self.config_loader.load_integration_config("ml", domain)
        else:
            config = self.config_loader.load_integration_config(source_type, domain)
        
        if not config:
            logger.warning(f"No configuration found for source type '{source_type}'{' in domain ' + domain if domain else ''}")
            return None
        
        # Get the configuration for this specific source
        sources = config.get(source_type, {}).get("sources", {})
        source_config = sources.get(source_id)
        
        if not source_config:
            # If domain-specific config not found, try global config (only if domain was specified)
            if domain:
                return self.get_data_source_config(source_type, source_id, None)
            logger.warning(f"No configuration found for source '{source_id}' of type '{source_type}'{' in domain ' + domain if domain else ''}")
            return None
        
        # Cache the result
        self.source_cache[cache_key] = source_config
        return source_config
    
    def get_all_data_sources(self, source_type: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get all data source configurations for a type.
        
        Args:
            source_type: The type of data source
            domain: Optional domain name to fetch domain-specific configs
            
        Returns:
            A dictionary mapping source IDs to source configurations
        """
        config = None
        if source_type == "database":
            config = self.config_loader.load_database_config(domain)
        elif source_type == "api":
            config = self.config_loader.load_integration_config("api_sources", domain)
        elif source_type == "feast":
            config = self.config_loader.load_integration_config("feast_config", domain)
        elif source_type == "ml":
            config = self.config_loader.load_integration_config("ml", domain)
        else:
            config = self.config_loader.load_integration_config(source_type, domain)
        
        # Look for sources under the source_type key
        return config.get(source_type, {}).get("sources", {})
    
    def reload_data_source_config(self, source_type: Optional[str] = None, domain: Optional[str] = None) -> None:
        """Reload data source configurations from disk.
        
        Args:
            source_type: If provided, only reload this specific source type
            domain: If provided, only reload configs for this domain
        """
        # Clear cache entries based on source_type and domain
        if source_type and domain:
            # Clear specific domain and source type cache entries
            key_prefix = f"{domain}.{source_type}."
            for cache_key in list(self.source_cache.keys()):
                if cache_key.startswith(key_prefix):
                    del self.source_cache[cache_key]
        elif source_type:
            # Clear all cache entries for this source type across all domains
            for cache_key in list(self.source_cache.keys()):
                if cache_key.endswith(f".{source_type}.") or cache_key.startswith(f"{source_type}."):
                    del self.source_cache[cache_key]
        elif domain:
            # Clear all cache entries for this domain
            key_prefix = f"{domain}."
            for cache_key in list(self.source_cache.keys()):
                if cache_key.startswith(key_prefix):
                    del self.source_cache[cache_key]
        else:
            # Clear all cache entries
            self.source_cache.clear()
            
        # Reload configurations based on source_type
        if source_type:
            if domain:
                # Reload domain-specific configs for this source type
                if source_type == "database":
                    self.config_loader.reload_config(f"domains/{domain}/database.yaml")
                else:
                    config_file = f"domains/{domain}/integrations/{source_type}.yaml"
                    if source_type == "api":
                        config_file = f"domains/{domain}/integrations/api_sources.yaml"
                    elif source_type == "feast":
                        config_file = f"domains/{domain}/integrations/feast_config.yaml"
                    self.config_loader.reload_config(config_file)
            else:
                # Reload global configs for this source type
                if source_type == "database":
                    self.config_loader.reload_config("database.yaml")
                else:
                    config_file = f"integrations/{source_type}.yaml"
                    if source_type == "api":
                        config_file = "integrations/api_sources.yaml"
                    elif source_type == "feast":
                        config_file = "integrations/feast_config.yaml"
                    self.config_loader.reload_config(config_file)
        else:
            # Reload all configurations
            self.config_loader.reload_config()
        
        logger.info(f"Reloaded data source configurations{' for type ' + source_type if source_type else ''}{' in domain ' + domain if domain else ''}")
