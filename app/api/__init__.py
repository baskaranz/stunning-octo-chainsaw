from fastapi import APIRouter
from app.api.routes import router as api_router

# Main API router
router = APIRouter(prefix="/api")

# Include domain-specific routes
router.include_router(api_router)
