"""
Loan Prediction Example App Extension

This module contains the code to extend the basic orchestrator app with
loan prediction functionality.
"""

import os
from fastapi import FastAPI
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

def extend_app(app: FastAPI) -> FastAPI:
    """
    Extend the main app with loan prediction routes and functionality.
    
    This is called by the main.py when the LOAN_PREDICTION_EXAMPLE environment
    variable is set.
    """
    logger.info("Extending app with loan prediction functionality")
    
    # Only import controllers when needed to avoid core dependencies
    from examples.loan_prediction.controllers.loan_prediction_controller import router as loan_prediction_router
    
    # Add loan prediction routes
    app.include_router(loan_prediction_router, prefix="/api/loan-prediction", tags=["loan-prediction"])
    
    # Configure the database and model clients
    from app.config.data_source_config_manager import DataSourceConfigManager
    from app.adapters.database.database_client import DatabaseClient
    
    # Patch the data source config manager to include loan prediction configs
    original_init = DataSourceConfigManager.__init__
    
    def patched_init(self, *args, **kwargs):
        # Call the original __init__ method
        original_init(self, *args, **kwargs)
        
        # Add loan model configurations
        self.source_cache["ml.loan_model"] = {
            "base_url": "http://localhost:5001",
            "models": {
                "loan_approval": {
                    "endpoint": "/",
                    "timeout": 30,
                    "headers": {
                        "Content-Type": "application/json"
                    }
                }
            }
        }
        
        # Add API configuration
        self.source_cache["api.loan_model"] = {
            "base_url": "http://localhost:5001",
            "timeout": 30,
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        logger.info("Added loan model configurations to data source config manager")
    
    # Replace the __init__ method
    DataSourceConfigManager.__init__ = patched_init
    
    # Patch the database client to check for loan prediction database
    original_db_init = DatabaseClient.__init__
    
    def patched_db_init(self, *args, **kwargs):
        # Call the original __init__ method
        original_db_init(self, *args, **kwargs)
        
        # Add logic to check for loan_prediction.db
        loan_pred_path = os.path.join(os.getcwd(), "examples/loan_prediction/loan_prediction.db")
        if os.path.exists(loan_pred_path):
            # Replace the default engine with the loan prediction database
            connection_string = f"sqlite:///{loan_pred_path}"
            from sqlalchemy import create_engine
            engine = create_engine(
                connection_string,
                connect_args={"check_same_thread": False}
            )
            self.engines["default"] = engine
            logger.info(f"Using loan prediction database at: {loan_pred_path}")
    
    # Patch DatabaseClient.__init__ to use loan prediction database if available
    DatabaseClient.__init__ = patched_db_init
    
    # Add loan prediction specific methods to the DatabaseClient
    from examples.loan_prediction.database_extensions import patch_database_client
    patch_database_client()
    logger.info("Added loan prediction methods to database client")
    
    # Add loan prediction specific methods to the ModelClient
    from examples.loan_prediction.ml_extensions import patch_model_client
    patch_model_client()
    logger.info("Added loan prediction methods to model client")
    
    # Ensure the app uses our example config path
    if 'ORCHESTRATOR_CONFIG_PATH' not in os.environ:
        example_config_path = os.path.join(os.getcwd(), "examples/loan_prediction/config")
        os.environ['ORCHESTRATOR_CONFIG_PATH'] = example_config_path
        logger.info(f"Set orchestrator config path to: {example_config_path}")
    
    return app