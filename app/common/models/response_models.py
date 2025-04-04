from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

class CustomerResponse(BaseModel):
    """Response model for customer data."""
    customer_id: str = Field(..., description="Unique customer identifier")
    name: str = Field(..., description="Customer's full name")
    email: EmailStr = Field(..., description="Customer's email address")
    phone: Optional[str] = Field(None, description="Customer's phone number")
    address: Optional[str] = Field(None, description="Customer's address")
    date_of_birth: Optional[date] = Field(None, description="Customer's date of birth")
    created_at: datetime = Field(..., description="When the customer was created")
    updated_at: datetime = Field(..., description="When the customer was last updated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust_12345",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "address": "123 Main St, City, Country",
                "date_of_birth": "1990-01-01",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z"
            }
        }
