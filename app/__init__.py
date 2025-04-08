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
    
    return app
