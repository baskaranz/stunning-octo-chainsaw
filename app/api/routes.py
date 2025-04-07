from fastapi import APIRouter
from app.api.controllers.customer_controller import router as customer_router
from app.api.controllers.orchestrator_controller import router as orchestrator_router

# Main router for all API endpoints
router = APIRouter()

# Include domain-specific routers
router.include_router(customer_router, prefix="/customers", tags=["customers"])

# Include the generic orchestrator router for model scoring endpoints
router.include_router(orchestrator_router, prefix="/orchestrator", tags=["model-scoring"])
