from typing import Any, Dict, Optional
from fastapi import Depends

from app.config.config_loader import ConfigLoader
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class EndpointConfigManager:
    """Manages endpoint configurations for API operations."""
    
    def __init__(self, config_loader: ConfigLoader = Depends()):
        self.config_loader = config_loader
        self.endpoint_cache = {}
    
    def get_endpoint_config(self, domain: str, operation: str) -> Optional[Dict[str, Any]]:
        """Get the configuration for a specific domain operation endpoint.
        
        Args:
            domain: The business domain (e.g., "customers")
            operation: The operation type (e.g., "get", "list")
            
        Returns:
            The endpoint configuration or None if not found
        """
        # Check cache first
        cache_key = f"{domain}.{operation}"
        if cache_key in self.endpoint_cache:
            return self.endpoint_cache[cache_key]
        
        # Load domain configuration
        domain_config = self.config_loader.load_domain_config(domain)
        if not domain_config:
            logger.warning(f"No configuration found for domain '{domain}'")
            return None
        
        # Get the endpoint configuration for this operation
        endpoints = domain_config.get("endpoints", {})
        endpoint_config = endpoints.get(operation)
        
        if not endpoint_config:
            logger.warning(f"No configuration found for operation '{operation}' in domain '{domain}'")
            return None
        
        # Cache the result
        self.endpoint_cache[cache_key] = endpoint_config
        return endpoint_config
    
    def get_all_endpoints(self, domain: str) -> Dict[str, Any]:
        """Get all endpoint configurations for a domain.
        
        Args:
            domain: The business domain
            
        Returns:
            A dictionary mapping operation names to endpoint configurations
        """
        domain_config = self.config_loader.load_domain_config(domain)
        return domain_config.get("endpoints", {})
    
    def reload_endpoint_config(self, domain: Optional[str] = None) -> None:
        """Reload endpoint configurations from disk.
        
        Args:
            domain: If provided, only reload this specific domain
        """
        if domain:
            # Clear cache entries for this domain
            for cache_key in list(self.endpoint_cache.keys()):
                if cache_key.startswith(f"{domain}."):
                    del self.endpoint_cache[cache_key]
            
            # Reload the domain configuration
            self.config_loader.reload_config(f"domains/{domain}.yaml")
        else:
            # Clear all cache entries
            self.endpoint_cache.clear()
            
            # Reload all domain configurations
            self.config_loader.reload_config()
        
        logger.info(f"Reloaded endpoint configurations {'for domain ' + domain if domain else 'for all domains'}")
