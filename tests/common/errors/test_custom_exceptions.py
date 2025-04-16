import pytest
from app.common.errors.custom_exceptions import (
    OrchestratorError, ConfigurationError, DataSourceError,
    DatabaseError, ApiError, FeastError, ModelError,
    ValidationError, ResourceNotFoundError, AuthorizationError
)

def test_orchestrator_error():
    """Test the base OrchestratorError."""
    # Test basic initialization
    error = OrchestratorError("Test error message")
    assert error.message == "Test error message"
    assert str(error) == "Test error message"

def test_configuration_error():
    """Test ConfigurationError."""
    error = ConfigurationError("Missing config section")
    assert error.message == "Missing config section"
    assert isinstance(error, OrchestratorError)
    assert str(error) == "Missing config section"

def test_data_source_error():
    """Test DataSourceError with and without source name."""
    # Test with source name
    error = DataSourceError("Connection failed", "database", "mysql")
    assert error.source_type == "database"
    assert error.source_name == "mysql"
    assert "Connection failed" in str(error)
    assert "database/mysql" in str(error)
    
    # Test without source name
    error = DataSourceError("API timeout", "api")
    assert error.source_type == "api"
    assert error.source_name is None
    assert "API timeout" in str(error)
    assert "api" in str(error)

def test_database_error():
    """Test DatabaseError with and without source name."""
    # Test with source name
    error = DatabaseError("Query failed", "postgres")
    assert error.source_type == "database"
    assert error.source_name == "postgres"
    assert "Query failed" in str(error)
    
    # Test without source name
    error = DatabaseError("Connection timeout")
    assert error.source_type == "database"
    assert error.source_name is None
    assert "Connection timeout" in str(error)

def test_api_error():
    """Test ApiError with various combinations of parameters."""
    # Test with all parameters
    error = ApiError("Not found", "users_api", 404)
    assert error.source_type == "api"
    assert error.source_name == "users_api"
    assert error.status_code == 404
    assert "Not found" in str(error)
    assert "Status: 404" in str(error)
    
    # Test without status code
    error = ApiError("Connection failed", "orders_api")
    assert error.source_type == "api"
    assert error.source_name == "orders_api"
    assert error.status_code is None
    assert "Connection failed" in str(error)
    assert "Status" not in str(error)
    
    # Test without source name
    error = ApiError("Server error", status_code=500)
    assert error.source_type == "api"
    assert error.source_name is None
    assert error.status_code == 500
    assert "Server error" in str(error)
    assert "Status: 500" in str(error)

def test_feast_error():
    """Test FeastError with and without source name."""
    # Test with source name
    error = FeastError("Feature not found", "production")
    assert error.source_type == "feast"
    assert error.source_name == "production"
    assert "Feature not found" in str(error)
    
    # Test without source name
    error = FeastError("Registry unavailable")
    assert error.source_type == "feast"
    assert error.source_name is None
    assert "Registry unavailable" in str(error)

def test_model_error():
    """Test ModelError with and without source name."""
    # Test with source name
    error = ModelError("Prediction failed", "iris_model")
    assert error.source_type == "ml"
    assert error.source_name == "iris_model"
    assert "Prediction failed" in str(error)
    
    # Test without source name
    error = ModelError("Model not loaded")
    assert error.source_type == "ml"
    assert error.source_name is None
    assert "Model not loaded" in str(error)

def test_validation_error():
    """Test ValidationError with and without errors dict."""
    # Test with errors dictionary
    validation_errors = {
        "email": "Invalid email format",
        "age": "Must be a positive integer"
    }
    error = ValidationError("Validation failed", validation_errors)
    assert error.message == "Validation failed"
    assert error.errors == validation_errors
    assert str(error) == "Validation failed"
    
    # Test without errors dictionary
    error = ValidationError("Invalid input")
    assert error.message == "Invalid input"
    assert error.errors == {}
    assert str(error) == "Invalid input"

def test_resource_not_found_error():
    """Test ResourceNotFoundError."""
    error = ResourceNotFoundError("customer", "12345")
    assert error.resource_type == "customer"
    assert error.resource_id == "12345"
    assert "Customer with ID '12345' not found" in str(error)
    
    # Test with different resource type
    error = ResourceNotFoundError("product", "ABC123")
    assert error.resource_type == "product"
    assert error.resource_id == "ABC123"
    assert "Product with ID 'ABC123' not found" in str(error)

def test_authorization_error():
    """Test AuthorizationError."""
    error = AuthorizationError("Insufficient permissions")
    assert error.message == "Insufficient permissions"
    assert isinstance(error, OrchestratorError)
    assert str(error) == "Insufficient permissions"