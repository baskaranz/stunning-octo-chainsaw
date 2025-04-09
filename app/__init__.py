from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import router as api_router
from app.config.config_loader import ConfigLoader
from app.common.utils.logging_utils import get_logger
import os
import traceback

logger = get_logger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    
    # Print configuration path being used
    config_path = os.environ.get("CONFIG_PATH", os.environ.get("ORCHESTRATOR_CONFIG_PATH", "config"))
    logger.info(f"Using configuration path: {config_path}")
    
    # Initialize FastAPI app
    app = FastAPI(
        title="Orchestrator API Service",
        description="API service for orchestrating data flows across multiple sources",
        version="0.1.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add exception handler for detailed logging
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        error_detail = {
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "path": request.url.path
        }
        logger.error(f"Unhandled exception: {error_detail}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(exc)}
        )
    
    # Include API routes
    app.include_router(api_router)
    
    # Add debug route for testing
    @app.get("/debug")
    async def debug_route():
        logger.info("Debug route accessed")
        return {"status": "ok", "config_path": config_path}
        
    # Add domains route for accessing available domains
    @app.get("/orchestrator/domains")
    async def domains_route():
        from app.config.config_loader import ConfigLoader
        logger.info("Domains route accessed")
        config_loader = ConfigLoader()
        domains = config_loader.list_domain_configs()
        logger.info(f"Found domains: {domains}")
        return domains
    
    # Add startup and shutdown events
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup resources on application shutdown."""
        from app.adapters.ml.model_client import ModelClient
        from fastapi import Depends
        
        try:
            # Get the model client
            from fastapi.dependency_overrides import get_respository
            model_client = ModelClient()
            
            # Shutdown model client and unload all models
            logger.info("Shutting down model client and unloading models...")
            await model_client.shutdown()
            logger.info("Model client shutdown complete")
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")
    
    return app
