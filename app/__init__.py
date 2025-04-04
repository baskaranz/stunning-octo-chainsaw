from fastapi import FastAPI
from app.api import router as api_router
from app.config.config_loader import ConfigLoader

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Load configuration
    config = ConfigLoader().load_config()
    
    # Initialize FastAPI app
    app = FastAPI(
        title="Orchestrator API Service",
        description="API service for orchestrating data flows across multiple sources",
        version="0.1.0"
    )
    
    # Include API routes
    app.include_router(api_router)
    
    return app
