from fastapi import APIRouter
from app.api.controllers.customer_controller import router as customer_router
from app.api.controllers.orchestrator_controller import router as orchestrator_router

# Main router for all API endpoints
router = APIRouter()

# Include domain-specific routers
router.include_router(customer_router, prefix="/customers", tags=["customers"])

# Include the generic orchestrator router
router.include_router(orchestrator_router, prefix="/orchestrator", tags=["model-scoring"])

# Note: Loan prediction controller is included via the examples/loan_prediction/extend_app.py
# when the --with-loan-prediction flag or LOAN_PREDICTION_EXAMPLE env var is set
