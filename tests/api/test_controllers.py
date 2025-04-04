import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date
import json

# Test data
test_customer = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "address": "123 Main St, City, Country",
    "date_of_birth": "1990-01-01"
}

@pytest.mark.asyncio
async def test_create_customer(app_client, database_client, monkeypatch):
    """Test creating a customer."""
    # Mock database client to return a predefined response
    async def mock_create_customer(self, customer_data, source_id="default"):
        return {
            "customer_id": "cust_test123",
            "name": customer_data.get("name"),
            "email": customer_data.get("email"),
            "phone": customer_data.get("phone"),
            "address": customer_data.get("address"),
            "date_of_birth": customer_data.get("date_of_birth"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    # Apply the mock
    monkeypatch.setattr(database_client.__class__, "create_customer", mock_create_customer)
    
    # Make a request to create a customer
    response = app_client.post("/api/customers/", json=test_customer)
    
    # Check the response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == test_customer["name"]
    assert data["email"] == test_customer["email"]
    assert "customer_id" in data
    assert data["customer_id"] == "cust_test123"

@pytest.mark.asyncio
async def test_get_customer(app_client, database_client, monkeypatch):
    """Test getting a customer by ID."""
    # Mock database client to return a predefined response
    async def mock_get_customer(self, customer_id, source_id="default"):
        if customer_id == "cust_test123":
            return {
                "customer_id": customer_id,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "address": "123 Main St, City, Country",
                "date_of_birth": "1990-01-01",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        return None
    
    # Apply the mock
    monkeypatch.setattr(database_client.__class__, "get_customer", mock_get_customer)
    
    # Make a request to get an existing customer
    response = app_client.get("/api/customers/cust_test123")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john.doe@example.com"
    assert data["customer_id"] == "cust_test123"
    
    # Make a request to get a non-existent customer
    response = app_client.get("/api/customers/cust_nonexistent")
    
    # Check the response
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_list_customers(app_client, database_client, monkeypatch):
    """Test listing customers."""
    # Mock database client to return a predefined response
    async def mock_list_customers(self, limit=10, offset=0, source_id="default"):
        return [
            {
                "customer_id": "cust_test123",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "address": "123 Main St, City, Country",
                "date_of_birth": "1990-01-01",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "customer_id": "cust_test456",
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "+0987654321",
                "address": "456 Oak St, City, Country",
                "date_of_birth": "1985-05-15",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
    
    # Apply the mock
    monkeypatch.setattr(database_client.__class__, "list_customers", mock_list_customers)
    
    # Make a request to list customers
    response = app_client.get("/api/customers/")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "John Doe"
    assert data[1]["name"] == "Jane Smith"