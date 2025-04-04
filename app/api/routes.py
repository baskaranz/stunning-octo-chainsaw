from fastapi import APIRouter
from app.api.controllers.customer_controller import router as customer_router

# Main router for all API endpoints
router = APIRouter()

# Include domain-specific routers
router.include_router(customer_router, prefix="/customers", tags=["customers"])
