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
        from app.config.config_loader import ConfigLoader
        
        logger.info(f"Debug endpoint route accessed for {domain}/{operation}")
        
        # Create instances directly
        config_loader = ConfigLoader()
        config_mgr = EndpointConfigManager(config_loader)
        
        # Check if domain exists
        domains = config_loader.list_domain_configs()
        domain_exists = domain in domains
        
        # Get endpoint config if domain exists
        config = None
        if domain_exists:
            config = config_mgr.get_endpoint_config(domain, operation)
        
        if config:
            logger.info(f"Found endpoint config for {domain}/{operation}")
            return {
                "status": "ok",
                "domain": domain,
                "operation": operation,
                "domain_exists": domain_exists,
                "config_found": True,
                "config": config
            }
        else:
            logger.warning(f"No endpoint config found for {domain}/{operation}")
            return {
                "status": "error",
                "domain": domain,
                "operation": operation,
                "domain_exists": domain_exists,
                "config_found": False,
                "domains_available": domains,
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
        from app.config.config_loader import ConfigLoader
        from app.config.endpoint_config_manager import EndpointConfigManager
        from app.orchestration.data_orchestrator import DataOrchestrator
        from app.orchestration.execution_tracker import ExecutionTracker
        from app.orchestration.response_assembler import ResponseAssembler
        
        logger.info(f"Iris test route accessed for flower_id {flower_id}")
        
        # Create all components directly without Depends
        config_loader = ConfigLoader()
        endpoint_config = EndpointConfigManager(config_loader)
        data_orchestrator = DataOrchestrator()
        execution_tracker = ExecutionTracker()
        response_assembler = ResponseAssembler()
        
        # Create the request processor with manually injected dependencies
        processor = RequestProcessor(
            endpoint_config=endpoint_config,
            data_orchestrator=data_orchestrator,
            execution_tracker=execution_tracker,
            response_assembler=response_assembler
        )
        
        # Load domain config directly to check it exists
        domain_config = config_loader.load_domain_config("iris_example")
        
        if not domain_config:
            return {
                "status": "error",
                "message": "Domain 'iris_example' not found in configuration",
                "available_domains": config_loader.list_domain_configs()
            }
        
        # Check endpoint exists in domain config
        endpoints = domain_config.get("endpoints", {})
        if "predict" not in endpoints:
            return {
                "status": "error",
                "message": "Endpoint 'predict' not found in domain 'iris_example'",
                "available_endpoints": list(endpoints.keys())
            }
        
        # Process the request
        try:
            result = await processor.process(
                domain="iris_example",
                operation="predict",
                request_data={
                    "path_params": {"flower_id": str(flower_id)},
                    "query_params": {},
                    "body": {}
                }
            )
            return result
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            import traceback
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    # Add direct sample route
    @app.get("/orchestrator/iris-direct/samples")
    async def iris_samples_route():
        from app.orchestration.request_processor import RequestProcessor
        from app.config.config_loader import ConfigLoader
        from app.config.endpoint_config_manager import EndpointConfigManager
        from app.orchestration.data_orchestrator import DataOrchestrator
        from app.orchestration.execution_tracker import ExecutionTracker
        from app.orchestration.response_assembler import ResponseAssembler
        
        logger.info("Iris samples route accessed")
        
        # Create all components directly without Depends
        config_loader = ConfigLoader()
        endpoint_config = EndpointConfigManager(config_loader)
        data_orchestrator = DataOrchestrator()
        execution_tracker = ExecutionTracker()
        response_assembler = ResponseAssembler()
        
        # Create the request processor with manually injected dependencies
        processor = RequestProcessor(
            endpoint_config=endpoint_config,
            data_orchestrator=data_orchestrator,
            execution_tracker=execution_tracker,
            response_assembler=response_assembler
        )
        
        try:
            result = await processor.process(
                domain="iris_example",
                operation="samples",
                request_data={
                    "path_params": {},
                    "query_params": {"limit": "5"},
                    "body": {}
                }
            )
            return result
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            import traceback
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    # Add direct route for troubleshooting each endpoint type
    @app.get("/debug/troubleshoot-iris")
    async def troubleshoot_iris_route():
        from app.config.config_loader import ConfigLoader
        from app.config.endpoint_config_manager import EndpointConfigManager
        
        config_loader = ConfigLoader()
        endpoint_config = EndpointConfigManager(config_loader)
        
        # Collect comprehensive debugging information
        domains = config_loader.list_domain_configs()
        iris_config = config_loader.load_domain_config("iris_example")
        
        # Get available endpoints
        endpoints = {}
        if iris_config:
            endpoints = iris_config.get("endpoints", {})
        
        # Get database config
        db_config = config_loader.load_database_config("iris_example")
        
        # Get ML config
        ml_config = config_loader.load_integration_config("ml_config", "iris_example")
        
        # Return all debugging information
        return {
            "status": "ok",
            "domains_available": domains,
            "iris_domain_found": "iris_example" in domains,
            "iris_config": {
                "exists": bool(iris_config),
                "domain_id": iris_config.get("domain_id") if iris_config else None,
                "description": iris_config.get("description") if iris_config else None,
                "endpoints": list(endpoints.keys()) if endpoints else []
            },
            "database_config": {
                "exists": bool(db_config),
                "sources": list(db_config.get("database", {}).get("sources", {}).keys()) if db_config else [],
                "operations": list(db_config.get("database", {}).get("operations", {}).keys()) if db_config else []
            },
            "ml_config": {
                "exists": bool(ml_config),
                "sources": list(ml_config.get("ml", {}).get("sources", {}).keys()) if ml_config else []
            },
            "config_path": config_path
        }
        
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
