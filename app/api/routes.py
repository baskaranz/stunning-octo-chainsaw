from fastapi import APIRouter
from app.api.controllers.customer_controller import router as customer_router

# Main router for all API endpoints
router = APIRouter()

# Include domain-specific routers
router.include_router(customer_router, prefix="/customers", tags=["customers"])

# Loan prediction controller is included via the examples/loan_prediction/extend_app.py
# when the --with-loan-prediction flag or LOAN_PREDICTION_EXAMPLE env var is set
