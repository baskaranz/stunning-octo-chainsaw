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
    
    # Add endpoint config debug route
    @app.get("/debug/endpoint/{domain}/{operation}")
    async def debug_endpoint_route(domain: str, operation: str):
        from app.config.endpoint_config_manager import EndpointConfigManager
        logger.info(f"Debug endpoint route accessed for {domain}/{operation}")
        config_mgr = EndpointConfigManager()
        config = config_mgr.get_endpoint_config(domain, operation)
        if config:
            logger.info(f"Found endpoint config for {domain}/{operation}")
            return {
                "status": "ok",
                "domain": domain,
                "operation": operation,
                "config_found": True,
                "config": config
            }
        else:
            logger.warning(f"No endpoint config found for {domain}/{operation}")
            return {
                "status": "error",
                "domain": domain,
                "operation": operation,
                "config_found": False,
                "error": "Endpoint configuration not found"
            }
        
    # Add domains route for accessing available domains
    @app.get("/orchestrator/domains")
    async def domains_route():
        from app.config.config_loader import ConfigLoader
        logger.info("Domains route accessed")
        config_loader = ConfigLoader()
        domains = config_loader.list_domain_configs()
        logger.info(f"Found domains: {domains}")
        return domains
        
    # Add test iris routes for direct access
    @app.get("/orchestrator/iris-test/predict/{flower_id}")
    async def iris_test_route(flower_id: int):
        from app.orchestration.request_processor import RequestProcessor
        logger.info(f"Iris test route accessed for flower_id {flower_id}")
        processor = RequestProcessor()
        result = await processor.process(
            domain="iris_example",
            operation="predict",
            request_data={
                "path_params": {"domain": "iris_example", "operation": "predict", "flower_id": flower_id},
                "query_params": {},
                "body": {}
            }
        )
        return result
    
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
