from fastapi import APIRouter
from app.api.controllers.orchestrator_controller import router as orchestrator_router
from app.api.controllers.iris_controller import router as iris_router

# Main router for all API endpoints
router = APIRouter()

# Include the generic orchestrator router for model scoring endpoints
router.include_router(orchestrator_router, prefix="/orchestrator", tags=["model-scoring"])

# Include the direct iris API endpoints
router.include_router(iris_router, prefix="/api/iris", tags=["iris-example"])
