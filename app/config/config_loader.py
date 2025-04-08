import os
import yaml
import glob
from typing import Any, Dict, Optional, List
from pathlib import Path

from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ConfigLoader:
    """Loads and parses configuration files."""
    
    def __init__(self, config_dir: Optional[str] = None):
        # Check for CONFIG_PATH environment variable
        env_config_path = os.environ.get("CONFIG_PATH")
        if env_config_path and os.path.isfile(env_config_path):
            # If CONFIG_PATH points to a file, use its directory
            self.config_dir = os.path.dirname(env_config_path)
            logger.info(f"Using config directory from CONFIG_PATH: {self.config_dir}")
        else:
            # Check for CONFIG_DIR environment variable
            env_config_dir = os.environ.get("CONFIG_DIR")
            if env_config_dir and os.path.isdir(env_config_dir):
                self.config_dir = env_config_dir
                logger.info(f"Using config directory from CONFIG_DIR: {self.config_dir}")
            else:
                # Fall back to provided config_dir or default
                self.config_dir = config_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
                logger.info(f"Using default config directory: {self.config_dir}")
        
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
        
    def load_database_config(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Load database configuration.
        
        Args:
            domain: The domain name (if domain-specific database)
            
        Returns:
            The database configuration or an empty dict if not found
        """
        if domain:
            # First try domain-specific database config
            domain_db_config = self.load_yaml_file(f"domains/{domain}/database.yaml")
            if domain_db_config:
                return domain_db_config
                
        # Fallback to global database config (backward compatibility)
        return self.load_yaml_file("database.yaml")
    
    def load_integration_config(self, integration_type: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Load integration-specific configuration.
        
        Args:
            integration_type: The integration type (e.g., "api_sources")
            domain: The domain name (if domain-specific integration)
            
        Returns:
            The integration configuration or an empty dict if not found
        """
        if domain:
            # First try domain-specific integration config
            domain_config = self.load_yaml_file(f"domains/{domain}/integrations/{integration_type}.yaml")
            if domain_config:
                return domain_config
                
        # Fallback to global integration config (backward compatibility)
        return self.load_yaml_file(f"integrations/{integration_type}.yaml")
    
    def list_domain_configs(self) -> List[str]:
        """List all available domain configuration files.
        
        Returns:
            A list of domain names (without the .yaml extension)
        """
        domain_dir = os.path.join(self.config_dir, "domains")
        domain_files = glob.glob(os.path.join(domain_dir, "*.yaml"))
        
        # Extract domain names from filenames
        domain_names = []
        for filepath in domain_files:
            filename = os.path.basename(filepath)
            domain_name = os.path.splitext(filename)[0]
            domain_names.append(domain_name)
        
        return domain_names
    
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
