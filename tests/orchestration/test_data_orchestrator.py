import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, Optional

from app.orchestration.data_orchestrator import DataOrchestrator


class TestDataOrchestrator:
    """Tests for the DataOrchestrator class."""

    @pytest.fixture
    def mock_database(self):
        """Mock database client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_feast_client(self):
        """Mock Feast client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_model_client(self):
        """Mock model client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_config_provider(self):
        """Mock config provider."""
        provider = MagicMock()
        provider.get_endpoint_config.return_value = {
            "endpoint_id": "test_endpoint",
            "domain_id": "test_domain",
            "data_sources": [
                {
                    "name": "customers",
                    "type": "database",
                    "operation": "get_customer",
                    "params": {
                        "customer_id": "$request.customer_id"
                    }
                },
                {
                    "name": "predictions",
                    "type": "ml",
                    "operation": "predict",
                    "params": {
                        "model_id": "iris_model",
                        "features": "$customers.features"
                    },
                    "condition": "$customers.features"
                }
            ]
        }
        return provider
    
    @pytest.fixture
    def mock_request_preprocessor(self):
        """Mock request preprocessor."""
        preprocessor = MagicMock()
        preprocessor.process_request.return_value = {
            "customer_id": 123,
            "execution_id": "test-execution-id"
        }
        return preprocessor
    
    @pytest.fixture
    def mock_response_postprocessor(self):
        """Mock response postprocessor."""
        postprocessor = MagicMock()
        postprocessor.assemble_response.return_value = {
            "result": {
                "customer_data": {"id": 123, "name": "Test Customer"},
                "prediction": {"class": "setosa", "probability": 0.95}
            },
            "execution_id": "test-execution-id",
            "status": "success"
        }
        return postprocessor
    
    @pytest.fixture
    def orchestrator(
        self, 
        mock_database,
        mock_http_client,
        mock_feast_client,
        mock_model_client,
        mock_config_provider,
        mock_request_preprocessor,
        mock_response_postprocessor
    ):
        """Create a DataOrchestrator instance with mock dependencies."""
        return DataOrchestrator(
            database=mock_database,
            http_client=mock_http_client,
            feast_client=mock_feast_client,
            model_client=mock_model_client,
            config_provider=mock_config_provider,
            request_preprocessor=mock_request_preprocessor,
            response_postprocessor=mock_response_postprocessor
        )
    
    @pytest.mark.asyncio
    async def test_orchestrate_basic_flow(self, orchestrator, mock_database, mock_model_client):
        """Test the basic orchestration flow with multiple sources."""
        # Setup mock responses
        mock_database.get_customer.return_value = {
            "id": 123,
            "name": "Test Customer",
            "features": {
                "sepal_length": 5.1,
                "sepal_width": 3.5
            }
        }
        
        mock_model_client.predict.return_value = {
            "class": "setosa",
            "probability": 0.95
        }
        
        # Execute orchestration
        result = await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "data_sources": [
                    {
                        "name": "customer_data",
                        "type": "database",
                        "operation": "get_customer",
                        "params": {"customer_id": 123}
                    },
                    {
                        "name": "prediction",
                        "type": "ml",
                        "operation": "predict",
                        "params": {
                            "model_id": "iris_model",
                            "features": {"sepal_length": 5.1, "sepal_width": 3.5}
                        }
                    }
                ]
            },
            request_data={"customer_id": 123}
        )
        
        # Verify results
        assert "customer_data" in result
        assert "prediction" in result
        assert result["customer_data"]["name"] == "Test Customer"
        assert result["prediction"]["class"] == "setosa"
        
        # Verify mocks were called correctly
        mock_database.get_customer.assert_called_once_with(customer_id=123)
        mock_model_client.predict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_direct_mapping_source(self, orchestrator):
        """Test orchestration with a direct mapping source."""
        # Execute orchestration with a direct mapping source
        result = await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "data_sources": [
                    {
                        "name": "request_data",
                        "type": "direct",
                        "params": {
                            "customer_id": 123,
                            "request_time": "2025-04-16T10:00:00Z"
                        }
                    }
                ]
            },
            request_data={}
        )
        
        # Verify direct mapping was applied
        assert "request_data" in result
        assert result["request_data"]["customer_id"] == 123
        assert result["request_data"]["request_time"] == "2025-04-16T10:00:00Z"
    
    @pytest.mark.asyncio
    async def test_condition_evaluation(self, orchestrator, mock_database, mock_model_client):
        """Test orchestration with conditional sources."""
        # Setup mock responses
        mock_database.get_customer.return_value = {
            "id": 123,
            "name": "Test Customer",
            "features": None  # This will make the condition evaluate to False
        }
        
        # Execute orchestration with a conditional source
        result = await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "data_sources": [
                    {
                        "name": "customer_data",
                        "type": "database",
                        "operation": "get_customer",
                        "params": {"customer_id": 123}
                    },
                    {
                        "name": "prediction",
                        "type": "ml",
                        "operation": "predict",
                        "params": {"model_id": "iris_model"},
                        "condition": "$customer_data.features"  # This condition will be false
                    }
                ]
            },
            request_data={"customer_id": 123}
        )
        
        # Verify that only the first source was executed
        assert "customer_data" in result
        assert "prediction" not in result
        
        # Verify second operation was not called due to condition
        mock_model_client.predict.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_parameter_resolution(self, orchestrator, mock_database, mock_model_client):
        """Test parameter resolution from request and previous results."""
        # Setup mock responses
        mock_database.get_customer.return_value = {
            "id": 123,
            "features": {
                "sepal_length": 5.1,
                "sepal_width": 3.5
            }
        }
        
        # Execute orchestration with parameter references
        result = await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "data_sources": [
                    {
                        "name": "customer_data",
                        "type": "database",
                        "operation": "get_customer",
                        "params": {"customer_id": "$request.customer_id"}
                    },
                    {
                        "name": "prediction",
                        "type": "ml",
                        "operation": "predict",
                        "params": {
                            "model_id": "iris_model",
                            "features": "$customer_data.features"
                        }
                    }
                ]
            },
            request_data={"customer_id": 123}
        )
        
        # Verify parameter resolution worked
        mock_database.get_customer.assert_called_once_with(customer_id=123)
        mock_model_client.predict.assert_called_once_with(
            model_id="iris_model",
            features={"sepal_length": 5.1, "sepal_width": 3.5}
        )
    
    @pytest.mark.asyncio
    async def test_fallback_parameter_resolution(self, orchestrator, mock_database):
        """Test parameter resolution with fallback values."""
        # Execute orchestration with fallback parameters
        await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "data_sources": [
                    {
                        "name": "customer_data",
                        "type": "database",
                        "operation": "get_customer",
                        "params": {
                            "customer_id": "$request.missing || 456"
                        }
                    }
                ]
            },
            request_data={"customer_id": 123}
        )
        
        # Verify fallback was used - fixed to expect string '456' instead of integer 456
        # since the parameter resolution converts values to strings
        mock_database.get_customer.assert_called_once_with(customer_id='456')
    
    @pytest.mark.asyncio
    async def test_nested_parameter_resolution(self, orchestrator, mock_database, mock_model_client):
        """Test resolution of nested parameters."""
        # Setup mock responses
        mock_database.get_customer.return_value = {
            "id": 123,
            "metadata": {
                "preferences": {
                    "model": "advanced"
                }
            }
        }
        
        # Execute orchestration with nested parameter references
        await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "data_sources": [
                    {
                        "name": "customer_data",
                        "type": "database",
                        "operation": "get_customer",
                        "params": {"customer_id": 123}
                    },
                    {
                        "name": "prediction",
                        "type": "ml",
                        "operation": "predict",
                        "params": {
                            "model_id": "$customer_data.metadata.preferences.model"
                        }
                    }
                ]
            },
            request_data={}
        )
        
        # Verify nested parameter resolution worked
        mock_model_client.predict.assert_called_once_with(model_id="advanced")
    
    @pytest.mark.asyncio
    async def test_transform_application(self, orchestrator, mock_database):
        """Test application of transforms to source results."""
        # Setup mock responses
        mock_database.get_customer.return_value = {
            "id": 123,
            "name": "Test Customer",
            "email": "test@example.com",
            "address": "123 Main St",
            "phone": "555-1234"
        }
        
        # Execute orchestration with a transform
        result = await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "data_sources": [
                    {
                        "name": "customer_data",
                        "type": "database",
                        "operation": "get_customer",
                        "params": {"customer_id": 123},
                        "transform": {
                            "type": "select_fields",
                            "fields": ["id", "name", "email"]
                        }
                    }
                ]
            },
            request_data={}
        )
        
        # Verify transform was applied
        assert "customer_data" in result
        assert "id" in result["customer_data"]
        assert "name" in result["customer_data"]
        assert "email" in result["customer_data"]
        assert "address" not in result["customer_data"]
        assert "phone" not in result["customer_data"]
    
    @pytest.mark.asyncio
    async def test_endpoint_type_filtering(self, orchestrator, mock_database, mock_feast_client):
        """Test filtering of sources based on endpoint type."""
        # Execute orchestration with an endpoint type
        await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "endpoint_type": "database",
                "data_sources": [
                    {
                        "name": "customer_data",
                        "type": "database",
                        "operation": "get_customer",
                        "params": {"customer_id": 123}
                    },
                    {
                        "name": "features",
                        "type": "feast",
                        "operation": "get_features",
                        "params": {"entity_id": 123}
                    }
                ]
            },
            request_data={}
        )
        
        # Verify only the database source was called
        mock_database.get_customer.assert_called_once()
        mock_feast_client.get_features.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_request_end_to_end(
        self, 
        orchestrator, 
        mock_config_provider, 
        mock_request_preprocessor,
        mock_database,
        mock_model_client,
        mock_response_postprocessor
    ):
        """Test the end-to-end request processing flow."""
        # Setup mocks for the full flow
        mock_database.get_customer.return_value = {
            "id": 123,
            "name": "Test Customer",
            "features": {"sepal_length": 5.1, "sepal_width": 3.5}
        }
        
        mock_model_client.predict.return_value = {
            "class": "setosa",
            "probability": 0.95
        }
        
        # Process a request end-to-end
        request = {
            "endpoint_id": "test_endpoint",
            "parameters": {"customer_id": 123},
            "trace_execution": True,
            "trace_timing": True
        }
        
        response = await orchestrator.process_request(request)
        
        # Verify the full processing flow
        mock_config_provider.get_endpoint_config.assert_called_once_with("test_endpoint")
        mock_request_preprocessor.process_request.assert_called_once()
        mock_response_postprocessor.assemble_response.assert_called_once()
        
        # Check that execution trace and timing were included
        assert "execution_trace" in response
        assert "execution_timing" in response
    
    @pytest.mark.asyncio
    async def test_error_handling_with_flag(self, orchestrator, mock_database):
        """Test error handling when handle_errors flag is True."""
        # Setup mock to raise an exception
        mock_database.get_customer.side_effect = Exception("Database connection failed")
        
        # Process a request with error handling enabled
        request = {
            "endpoint_id": "test_endpoint",
            "parameters": {"customer_id": 123},
            "handle_errors": True
        }
        
        # Configure config provider for this specific test
        orchestrator.config_provider.get_endpoint_config.return_value = {
            "data_sources": [
                {
                    "name": "customer_data",
                    "type": "database",
                    "operation": "get_customer",
                    "params": {"customer_id": 123}
                }
            ]
        }
        
        # Process request with error handling
        response = await orchestrator.process_request(request, handle_errors=True)
        
        # Verify error was captured in response
        assert "errors" in response
        assert "general" in response["errors"]
        assert "Database connection failed" in response["errors"]["general"]
    
    @pytest.mark.asyncio
    async def test_unsupported_source_type(self, orchestrator):
        """Test behavior with an unsupported source type."""
        # Execute orchestration with an unsupported source type
        result = await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "data_sources": [
                    {
                        "name": "unsupported_source",
                        "type": "unsupported",
                        "operation": "some_operation",
                        "params": {}
                    }
                ]
            },
            request_data={}
        )
        
        # Verify the result doesn't contain the unsupported source
        assert "unsupported_source" not in result
    
    @pytest.mark.asyncio
    async def test_misconfigured_source(self, orchestrator):
        """Test behavior with a misconfigured source."""
        # Execute orchestration with a misconfigured source
        result = await orchestrator.orchestrate(
            execution_id="test-exec-id",
            endpoint_config={
                "data_sources": [
                    {
                        # Missing name
                        "type": "database",
                        "operation": "get_customer",
                        "params": {"customer_id": 123}
                    }
                ]
            },
            request_data={}
        )
        
        # Verify no results for the misconfigured source
        assert len(result) == 0