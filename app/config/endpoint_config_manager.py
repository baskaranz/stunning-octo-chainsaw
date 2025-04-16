from typing import Any, Dict, Optional, List
from fastapi import Depends

from app.config.config_loader import ConfigLoader
from app.orchestration.orchestration_interfaces import ConfigProvider
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Valid endpoint types
VALID_ENDPOINT_TYPES = ["database", "api", "feast", "ml", "composite"]

class EndpointConfigManager(ConfigProvider):
    """Manages endpoint configurations for API operations."""
    
    def __init__(self, config_loader: ConfigLoader = Depends()):
        self.config_loader = config_loader
        self.endpoint_cache = {}
        
    def get_endpoint_config(self, endpoint_id: str, domain: Optional[str] = None, 
                           version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get endpoint configuration by ID or domain/operation combination.
        
        This method implements the ConfigProvider interface and supports both:
        - New format: endpoint_id as the primary identifier (e.g. "customer_profile")
        - Legacy format: domain and operation as identifiers (e.g. "customers", "get")
        
        Args:
            endpoint_id: The endpoint ID or domain if using legacy format
            domain: Optional domain for versioned endpoints, or operation if using legacy format 
            version: Optional version identifier
            
        Returns:
            The endpoint configuration or None if not found
        """
        # First, try to interpret as new format with endpoint_id as the primary key
        if "." not in endpoint_id and domain is None:
            # Try to load by direct endpoint ID if no domain is provided
            for d in self.config_loader.get_all_domains():
                domain_config = self.config_loader.load_domain_config(d)
                endpoints = domain_config.get("endpoints", {})
                
                # Check if any endpoint has this ID
                for op, config in endpoints.items():
                    if config.get("endpoint_id") == endpoint_id:
                        # Found the endpoint by ID
                        self._validate_endpoint_config(config, d, op)
                        return config
            
            # If endpoint not found by ID, try to interpret as a domain name
            logger.debug(f"No endpoint found with ID '{endpoint_id}', checking if it's a domain")
        
        # Legacy format: domain.operation
        if domain is not None:
            # Use the first parameter as domain and second as operation
            return self.get_domain_operation_config(endpoint_id, domain)
            
        return None
        
    def get_domain_operation_config(self, domain: str, operation: str) -> Optional[Dict[str, Any]]:
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
        
        # Validate endpoint type
        self._validate_endpoint_config(endpoint_config, domain, operation)
        
        # Cache the result
        self.endpoint_cache[cache_key] = endpoint_config
        return endpoint_config
    
    def _validate_endpoint_config(self, endpoint_config: Dict[str, Any], domain: str, operation: str) -> None:
        """Validate the endpoint configuration.
        
        Args:
            endpoint_config: The endpoint configuration to validate
            domain: The domain name (for logging)
            operation: The operation name (for logging)
        """
        # Validate endpoint type
        endpoint_type = endpoint_config.get("endpoint_type")
        if not endpoint_type:
            # For backward compatibility, infer the endpoint type from data sources
            data_sources = endpoint_config.get("data_sources", [])
            if len(data_sources) > 1:
                endpoint_type = "composite"
                endpoint_config["endpoint_type"] = endpoint_type
            elif len(data_sources) == 1:
                endpoint_type = data_sources[0].get("type")
                endpoint_config["endpoint_type"] = endpoint_type
            else:
                logger.warning(f"No data sources found for endpoint '{operation}' in domain '{domain}'")
                endpoint_type = "unknown"
                endpoint_config["endpoint_type"] = endpoint_type
        
        # Check if the endpoint type is valid
        if endpoint_type not in VALID_ENDPOINT_TYPES:
            logger.warning(
                f"Invalid endpoint type '{endpoint_type}' for operation '{operation}' in domain '{domain}'. "
                f"Valid types are: {', '.join(VALID_ENDPOINT_TYPES)}"
            )
        
        # Ensure data sources are consistent with the endpoint type (except for composite)
        if endpoint_type != "composite":
            for data_source in endpoint_config.get("data_sources", []):
                source_type = data_source.get("type")
                if source_type != endpoint_type:
                    logger.warning(
                        f"Data source type '{source_type}' does not match endpoint type '{endpoint_type}' "
                        f"for operation '{operation}' in domain '{domain}'"
                    )
    
    def get_endpoint_by_type(self, domain: str, endpoint_type: str) -> Dict[str, Dict[str, Any]]:
        """Get all endpoints of a specific type for a domain.
        
        Args:
            domain: The business domain
            endpoint_type: The type of endpoint to filter by
            
        Returns:
            A dictionary mapping operation names to endpoint configurations
        """
        all_endpoints = self.get_all_endpoints(domain)
        filtered_endpoints = {}
        
        for operation, config in all_endpoints.items():
            # Get or infer the endpoint type
            config_type = config.get("endpoint_type")
            if not config_type:
                data_sources = config.get("data_sources", [])
                if len(data_sources) > 1:
                    config_type = "composite"
                elif len(data_sources) == 1:
                    config_type = data_sources[0].get("type")
                else:
                    config_type = "unknown"
            
            # Add to filtered results if type matches
            if config_type == endpoint_type:
                filtered_endpoints[operation] = config
        
        return filtered_endpoints
    
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
