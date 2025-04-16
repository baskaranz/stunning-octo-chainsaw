"""
Application factory module for Orkestra
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import traceback
import logging
import importlib.util

# Set up logger
logger = logging.getLogger(__name__)

# Global app instance
app = None

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    global app
    
    # Initialize FastAPI app
    app = FastAPI(
        title="Orkestra",
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
    
    # Print configuration path being used
    config_path = os.environ.get("CONFIG_PATH", os.environ.get("ORKESTRA_CONFIG_PATH", "config"))
    logger.info(f"Using configuration path: {config_path}")
    
    # Try to import app modules
    try:
        # Check if we're using the local app or library app
        if importlib.util.find_spec("app.api"):
            # Local app structure
            from app.api import router as api_router
            logger.info("Using local app.api router")
        else:
            # Library app structure
            from orkestra.app.api import router as api_router
            logger.info("Using library app.api router")
            
        # Include API routes
        app.include_router(api_router)
        
    except ImportError as e:
        logger.error(f"Error importing API router: {e}")
        
        # Add a placeholder route to indicate the error
        @app.get("/")
        async def root():
            return {
                "status": "error",
                "message": "API router could not be loaded. Please check your installation.",
                "error": str(e)
            }
    
    # Add a health check route
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    # Add debug route
    @app.get("/debug")
    async def debug_route():
        """Debug route for testing configuration"""
        logger.info("Debug route accessed")
        
        # Check config path and list available files
        config_files = []
        if os.path.exists(config_path):
            for root, dirs, files in os.walk(config_path):
                for file in files:
                    if file.endswith(".yaml") or file.endswith(".yml"):
                        config_files.append(os.path.join(root, file))
        
        return {
            "status": "ok",
            "config_path": config_path,
            "config_path_exists": os.path.exists(config_path),
            "config_files": config_files
        }
    
    return app