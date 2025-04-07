from fastapi import APIRouter, Depends, Path
from typing import Dict, Any

from app.orchestration.request_processor import RequestProcessor

router = APIRouter()

@router.get("/predict/{applicant_id}")
async def predict_loan_approval(
    applicant_id: str = Path(..., description="The applicant ID"),
    request_processor: RequestProcessor = Depends()
):
    """Predict loan approval probability for an applicant."""
    # Process the request through the orchestrator
    result = await request_processor.process(
        domain="loan_prediction",
        operation="predict",
        request_data={
            "path_params": {"applicant_id": applicant_id},
            "query_params": {},
            "body": {}
        }
    )
    
    return result

@router.get("/{applicant_id}")
async def get_applicant_data(
    applicant_id: str = Path(..., description="The applicant ID"),
    request_processor: RequestProcessor = Depends()
):
    """Get detailed applicant data."""
    # Process the request through the orchestrator
    result = await request_processor.process(
        domain="loan_prediction",
        operation="get_applicant_data",
        request_data={
            "path_params": {"applicant_id": applicant_id},
            "query_params": {},
            "body": {}
        }
    )
    
    return result