"""
Generic Orchestrator Example - App Extension

This module contains the code to extend the basic orchestrator app with
the generic orchestrator example functionality.
"""

import os
from fastapi import FastAPI
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

def extend_app(app: FastAPI) -> FastAPI:
    """
    Extend the main app with generic orchestrator example functionality.
    
    This function is designed to be called from main.py when the
    GENERIC_ORCHESTRATOR_EXAMPLE environment variable is set or the
    --with-generic-orchestrator flag is used.
    """
    logger.info("Extending app with generic orchestrator example functionality")
    
    # Configure the database and model clients
    from app.config.data_source_config_manager import DataSourceConfigManager
    from app.adapters.database.database_client import DatabaseClient
    
    # Patch the data source config manager to include ML configurations
    original_init = DataSourceConfigManager.__init__
    
    def patched_init(self, *args, **kwargs):
        # Call the original __init__ method
        original_init(self, *args, **kwargs)
        
        # Add credit risk model configuration
        self.source_cache["ml.credit_risk_model"] = {
            "base_url": "http://localhost:5003",
            "models": {
                "default": {
                    "endpoint": "/predict",
                    "timeout": 30,
                    "headers": {
                        "Content-Type": "application/json"
                    }
                }
            }
        }
        
        # Add product recommender model configuration
        self.source_cache["ml.product_recommender"] = {
            "base_url": "http://localhost:5004",
            "models": {
                "default": {
                    "endpoint": "/recommend",
                    "timeout": 30,
                    "headers": {
                        "Content-Type": "application/json"
                    }
                }
            }
        }
        
        logger.info("Added model configurations for generic orchestrator example")
    
    # Replace the __init__ method
    DataSourceConfigManager.__init__ = patched_init
    
    # Patch the database client to use the example database
    original_db_init = DatabaseClient.__init__
    
    def patched_db_init(self, *args, **kwargs):
        # Call the original __init__ method
        original_db_init(self, *args, **kwargs)
        
        # Look for the example database
        example_db_path = os.path.join(os.getcwd(), "examples/generic_orchestrator/orchestrator_example.db")
        if os.path.exists(example_db_path):
            # Replace the default engine with the example database
            connection_string = f"sqlite:///{example_db_path}"
            from sqlalchemy import create_engine
            engine = create_engine(
                connection_string,
                connect_args={"check_same_thread": False}
            )
            self.engines["default"] = engine
            logger.info(f"Using generic orchestrator example database at: {example_db_path}")
    
    # Patch DatabaseClient.__init__ to use the example database if available
    DatabaseClient.__init__ = patched_db_init
    
    # Add database methods for the example
    from examples.generic_orchestrator.database_extensions import patch_database_client
    patch_database_client()
    logger.info("Added database methods for generic orchestrator example")
    
    return app