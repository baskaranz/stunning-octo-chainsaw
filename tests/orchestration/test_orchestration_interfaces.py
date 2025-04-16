import pytest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, AsyncMock

from app.orchestration.orchestration_interfaces import (
    ConfigProvider, RequestPreprocessor, ResponsePostprocessor, Orchestrator
)

class TestConfigProvider:
    """Tests for the ConfigProvider Protocol."""
    
    def test_config_provider_implementation(self):
        """Test a concrete implementation of ConfigProvider."""
        # Create a concrete implementation of the ConfigProvider protocol
        class ConcreteConfigProvider:
            def get_endpoint_config(self, endpoint_id: str, domain: Optional[str] = None, 
                                  version: Optional[str] = None) -> Optional[Dict[str, Any]]:
                if endpoint_id == "test_endpoint":
                    return {"name": "Test Endpoint", "domain_id": domain, "version": version}
                return None
        
        # Instantiate the concrete implementation
        provider = ConcreteConfigProvider()
        
        # Test the implementation
        config = provider.get_endpoint_config("test_endpoint", domain="test_domain", version="v1")
        assert config is not None
        assert config["name"] == "Test Endpoint"
        assert config["domain_id"] == "test_domain"
        assert config["version"] == "v1"
        
        # Test with a non-existent endpoint
        config = provider.get_endpoint_config("non_existent")
        assert config is None
    
    def test_config_provider_with_mock(self):
        """Test ConfigProvider using a mock object."""
        # Create a mock that satisfies the ConfigProvider protocol
        mock_provider = MagicMock(spec=["get_endpoint_config"])
        mock_provider.get_endpoint_config.return_value = {
            "name": "Mock Endpoint",
            "data_sources": [{"type": "database", "name": "customer_data"}]
        }
        
        # Use the mock
        config = mock_provider.get_endpoint_config("any_endpoint")
        assert config["name"] == "Mock Endpoint"
        assert len(config["data_sources"]) == 1
        assert config["data_sources"][0]["type"] == "database"
        
        # Verify the mock was called correctly
        mock_provider.get_endpoint_config.assert_called_once_with("any_endpoint")


class TestRequestPreprocessor:
    """Tests for the RequestPreprocessor Protocol."""
    
    def test_request_preprocessor_implementation(self):
        """Test a concrete implementation of RequestPreprocessor."""
        # Create a concrete implementation
        class ConcreteRequestPreprocessor:
            def process_request(self, endpoint_config: Dict[str, Any], 
                              parameters: Dict[str, Any], 
                              execution_id: str) -> Dict[str, Any]:
                # Example: Add default values for missing parameters
                result = parameters.copy()
                if "default_params" in endpoint_config:
                    for key, value in endpoint_config["default_params"].items():
                        if key not in result:
                            result[key] = value
                
                # Add execution ID to the processed request
                result["execution_id"] = execution_id
                return result
        
        # Instantiate the concrete implementation
        preprocessor = ConcreteRequestPreprocessor()
        
        # Test the implementation
        endpoint_config = {
            "default_params": {"limit": 10, "offset": 0}
        }
        parameters = {"query": "test", "limit": 20}
        result = preprocessor.process_request(endpoint_config, parameters, "exec-123")
        
        # Verify the result contains all expected parameters
        assert result["query"] == "test"
        assert result["limit"] == 20  # Not overridden by default
        assert result["offset"] == 0  # Added from defaults
        assert result["execution_id"] == "exec-123"  # Added by the preprocessor
    
    def test_request_preprocessor_with_mock(self):
        """Test RequestPreprocessor using a mock object."""
        # Create a mock
        mock_preprocessor = MagicMock(spec=["process_request"])
        mock_preprocessor.process_request.return_value = {
            "processed": True,
            "query": "enhanced_query"
        }
        
        # Use the mock
        result = mock_preprocessor.process_request({}, {"query": "original"}, "exec-id")
        
        # Verify the result
        assert result["processed"] is True
        assert result["query"] == "enhanced_query"
        
        # Verify the mock was called correctly
        mock_preprocessor.process_request.assert_called_once()


class TestResponsePostprocessor:
    """Tests for the ResponsePostprocessor Protocol."""
    
    def test_response_postprocessor_implementation(self):
        """Test a concrete implementation of ResponsePostprocessor."""
        # Create a concrete implementation
        class ConcreteResponsePostprocessor:
            def assemble_response(self, endpoint_config: Dict[str, Any], 
                               data_result: Dict[str, Any],
                               execution_id: Optional[str] = None) -> Dict[str, Any]:
                # Example: Format the response according to a response template
                if "response_template" in endpoint_config:
                    template = endpoint_config["response_template"]
                    if template == "simple":
                        return {
                            "data": data_result,
                            "execution_id": execution_id,
                            "success": True
                        }
                
                # Default return the data as is
                return data_result
        
        # Instantiate the concrete implementation
        postprocessor = ConcreteResponsePostprocessor()
        
        # Test with a template
        endpoint_config = {
            "response_template": "simple"
        }
        data_result = {"customers": [{"id": 1, "name": "Test"}]}
        result = postprocessor.assemble_response(endpoint_config, data_result, "exec-123")
        
        # Verify the formatted response
        assert result["data"] == data_result
        assert result["execution_id"] == "exec-123"
        assert result["success"] is True
        
        # Test without a template
        endpoint_config = {}
        result = postprocessor.assemble_response(endpoint_config, data_result)
        
        # Verify the raw response
        assert result == data_result
    
    def test_response_postprocessor_with_mock(self):
        """Test ResponsePostprocessor using a mock object."""
        # Create a mock
        mock_postprocessor = MagicMock(spec=["assemble_response"])
        mock_postprocessor.assemble_response.return_value = {
            "formatted": True,
            "data": {"key": "value"}
        }
        
        # Use the mock
        result = mock_postprocessor.assemble_response({}, {"raw": True})
        
        # Verify the result
        assert result["formatted"] is True
        assert "data" in result
        
        # Verify the mock was called correctly
        mock_postprocessor.assemble_response.assert_called_once()


class TestOrchestrator:
    """Tests for the Orchestrator Protocol."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_implementation(self):
        """Test a concrete implementation of Orchestrator."""
        # Create a concrete implementation
        class ConcreteOrchestrator:
            async def orchestrate(self, execution_id: str, 
                               endpoint_config: Dict[str, Any],
                               request_data: Dict[str, Any]) -> Dict[str, Any]:
                # Example: Simple orchestration that combines data from specified sources
                result = {}
                
                # Process each data source defined in the config
                for source in endpoint_config.get("data_sources", []):
                    source_name = source.get("name")
                    if source_name:
                        # In a real implementation, this would call external services
                        # For testing, we just echo back the source configuration
                        result[source_name] = {
                            "config": source,
                            "request_data": request_data
                        }
                
                return result
        
        # Instantiate the concrete implementation
        orchestrator = ConcreteOrchestrator()
        
        # Test the implementation
        endpoint_config = {
            "data_sources": [
                {"name": "database", "type": "database", "operation": "query"},
                {"name": "ml", "type": "ml", "operation": "predict"}
            ]
        }
        request_data = {"customer_id": 123}
        
        result = await orchestrator.orchestrate("exec-123", endpoint_config, request_data)
        
        # Verify the result contains outputs for each source
        assert "database" in result
        assert "ml" in result
        assert result["database"]["config"]["type"] == "database"
        assert result["ml"]["config"]["type"] == "ml"
        assert result["database"]["request_data"]["customer_id"] == 123
    
    @pytest.mark.asyncio
    async def test_orchestrator_with_mock(self):
        """Test Orchestrator using a mock object."""
        # Create a mock using AsyncMock instead of MagicMock for async methods
        mock_orchestrator = AsyncMock()
        mock_orchestrator.orchestrate.return_value = {
            "orchestrated": True,
            "sources": ["database", "ml"]
        }
        
        # Call the async mock function
        result = await mock_orchestrator.orchestrate("exec-id", {}, {})
        
        # Verify the result
        assert result["orchestrated"] is True
        assert "database" in result["sources"]
        
        # Verify the mock was called correctly
        mock_orchestrator.orchestrate.assert_called_once_with("exec-id", {}, {})