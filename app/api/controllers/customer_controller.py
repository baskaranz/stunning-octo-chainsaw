from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.common.models.request_models import CustomerRequest
from app.common.models.response_models import CustomerResponse
from app.orchestration.request_processor import RequestProcessor

router = APIRouter()

@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    request_processor: RequestProcessor = Depends()
):
    """
    Retrieve a list of customers.
    """
    return await request_processor.process(
        "customers", 
        "list", 
        {"limit": limit, "offset": offset}
    )

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    request_processor: RequestProcessor = Depends()
):
    """
    Retrieve a single customer by ID.
    """
    result = await request_processor.process(
        "customers", 
        "get", 
        {"customer_id": customer_id}
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return result

@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer: CustomerRequest,
    request_processor: RequestProcessor = Depends()
):
    """
    Create a new customer.
    """
    return await request_processor.process(
        "customers", 
        "create", 
        customer.model_dump()
    )

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer: CustomerRequest,
    request_processor: RequestProcessor = Depends()
):
    """
    Update an existing customer.
    """
    data = customer.model_dump()
    data["customer_id"] = customer_id
    
    result = await request_processor.process(
        "customers", 
        "update", 
        data
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return result