from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.adapters.database.database_client import DatabaseClient
from app.common.errors.custom_exceptions import DatabaseError

router = APIRouter()

# Customer models
class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None

class CustomerResponse(BaseModel):
    customer_id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

def format_datetime_fields(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format datetime fields in customer data to ISO format strings."""
    result = dict(customer_data)
    for field in ['created_at', 'updated_at']:
        if field in result and isinstance(result[field], datetime):
            result[field] = result[field].isoformat()
    return result

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
    database_client: DatabaseClient = Depends()
) -> Dict[str, Any]:
    """Create a new customer."""
    try:
        customer_data = customer.model_dump()
        result = await database_client.create_customer(customer_data)
        return format_datetime_fields(result)
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer: {str(e)}"
        )

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    database_client: DatabaseClient = Depends()
) -> Dict[str, Any]:
    """Get a customer by ID."""
    try:
        result = await database_client.get_customer(customer_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )
        return format_datetime_fields(result)
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving customer: {str(e)}"
        )

@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    limit: int = 10,
    offset: int = 0,
    database_client: DatabaseClient = Depends()
) -> List[Dict[str, Any]]:
    """List customers with pagination."""
    try:
        result = await database_client.list_customers(limit, offset)
        return [format_datetime_fields(customer) for customer in result]
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing customers: {str(e)}"
        )