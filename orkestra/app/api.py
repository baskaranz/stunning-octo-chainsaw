"""
API routes for the Orkestra service
"""
from fastapi import APIRouter, Depends, HTTPException
import logging
import os
import importlib.util

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Check if the full app structure exists
try:
    # Try to import the actual API routes from the main app
    if importlib.util.find_spec("app.api.routes"):
        # Local app structure
        from app.api.routes import router as app_router
        logger.info("Using routes from local app.api.routes")
        router.include_router(app_router)
    elif importlib.util.find_spec("orkestra.app.routes"):
        # Library app structure
        from orkestra.app.routes import router as lib_router
        logger.info("Using routes from library orkestra.app.routes")
        router.include_router(lib_router)
    else:
        # Add placeholder route if neither is found
        @router.get("/")
        async def root():
            return {
                "message": "Orkestra is running, but no routes were loaded",
                "status": "warning"
            }
        
        # Add orchestrator info route
        @router.get("/orkestra/info")
        async def orchestrator_info():
            """Get information about the Orkestra service"""
            
            # Check configuration directory
            config_path = os.environ.get("CONFIG_PATH", os.environ.get("ORKESTRA_CONFIG_PATH", "config"))
            domains_dir = os.path.join(config_path, "domains")
            
            domains = []
            if os.path.exists(domains_dir):
                for file in os.listdir(domains_dir):
                    if file.endswith(".yaml") or file.endswith(".yml"):
                        domains.append(file.rsplit(".", 1)[0])
            
            return {
                "status": "ok",
                "version": "0.1.0",
                "config_path": config_path,
                "domains": domains
            }
        
except ImportError as e:
    logger.error(f"Error importing app routes: {e}")
    
    # Add placeholder route if import fails
    @router.get("/")
    async def root():
        return {
            "message": "Orkestra is running, but could not load routes",
            "status": "error",
            "error": str(e)
        }