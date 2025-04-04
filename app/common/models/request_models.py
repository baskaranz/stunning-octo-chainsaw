from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

class CustomerRequest(BaseModel):
    """Request model for customer data."""
    name: str = Field(..., description="Customer's full name")
    email: EmailStr = Field(..., description="Customer's email address")
    phone: Optional[str] = Field(None, description="Customer's phone number")
    address: Optional[str] = Field(None, description="Customer's address")
    date_of_birth: Optional[date] = Field(None, description="Customer's date of birth")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "address": "123 Main St, City, Country",
                "date_of_birth": "1990-01-01"
            }
        }
