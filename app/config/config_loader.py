import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path

from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ConfigLoader:
    """Loads and parses configuration files."""
    
    def __init__(self, config_dir: Optional[str] = None):
        # Default to the config directory in the project root
        self.config_dir = config_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
        self.config_cache = {}
    
    def load_config(self) -> Dict[str, Any]:
        """Load the global configuration."""
        return self.load_yaml_file("config.yaml")
    
    def load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file.
        
        Args:
            filename: The name of the file relative to the config directory
            
        Returns:
            The parsed configuration or an empty dict on error
        """
        # Check if already cached
        if filename in self.config_cache:
            return self.config_cache[filename]
        
        filepath = os.path.join(self.config_dir, filename)
        
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Configuration file not found: {filepath}")
                return {}
            
            with open(filepath, "r") as file:
                config = yaml.safe_load(file) or {}
                
            # Cache the result
            self.config_cache[filename] = config
            return config
        except Exception as e:
            logger.error(f"Error loading configuration file {filepath}: {str(e)}")
            return {}
    
    def load_domain_config(self, domain: str) -> Dict[str, Any]:
        """Load domain-specific configuration.
        
        Args:
            domain: The domain name (e.g., "customers")
            
        Returns:
            The domain configuration or an empty dict if not found
        """
        return self.load_yaml_file(f"domains/{domain}.yaml")
    
    def load_integration_config(self, integration_type: str) -> Dict[str, Any]:
        """Load integration-specific configuration.
        
        Args:
            integration_type: The integration type (e.g., "api_sources")
            
        Returns:
            The integration configuration or an empty dict if not found
        """
        return self.load_yaml_file(f"integrations/{integration_type}.yaml")
    
    def reload_config(self, filename: Optional[str] = None) -> None:
        """Reload configuration from disk.
        
        Args:
            filename: If provided, only reload this specific file
        """
        if filename:
            if filename in self.config_cache:
                del self.config_cache[filename]
        else:
            self.config_cache.clear()
        
        logger.info(f"Reloaded configuration {'for ' + filename if filename else 'for all files'}")
