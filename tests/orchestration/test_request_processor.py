import pytest
from unittest.mock import MagicMock, AsyncMock
import json
from datetime import datetime

from app.orchestration.request_processor import RequestProcessor
from app.orchestration.data_orchestrator import DataOrchestrator
from app.orchestration.execution_tracker import ExecutionTracker
from app.orchestration.response_assembler import ResponseAssembler
from app.config.endpoint_config_manager import EndpointConfigManager
from app.orchestration.orchestration_interfaces import Orchestrator

@pytest.mark.asyncio
async def test_process_basic_request():
    """Test processing a basic request through the orchestration pipeline."""
    # Mock dependencies
    config_manager = MagicMock(spec=EndpointConfigManager)
    orchestrator = AsyncMock(spec=Orchestrator)
    execution_tracker = MagicMock(spec=ExecutionTracker)
    response_assembler = MagicMock(spec=ResponseAssembler)
    
    # Set up mock behaviors
    config_manager.get_endpoint_config.return_value = {
        "data_sources": [
            {
                "name": "customer_data",
                "type": "database",
                "operation": "get_customer",
                "params": {
                    "customer_id": "$request.customer_id"
                }
            }
        ],
        "primary_source": "customer_data"
    }
    
    execution_tracker.start_execution.return_value = "exec_123"
    
    customer_data = {
        "customer_id": "cust_123",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    orchestrator.orchestrate.return_value = {
        "customer_data": customer_data
    }
    
    response_assembler.assemble_response.return_value = customer_data
    
    # Create the request processor
    processor = RequestProcessor(
        config_manager=config_manager,
        orchestrator=orchestrator,
        execution_tracker=execution_tracker,
        response_assembler=response_assembler
    )
    
    # Process a request
    request_data = {"customer_id": "cust_123"}
    result = await processor.process("customers", "get", request_data)
    
    # Verify the result
    assert result == customer_data
    
    # Verify the interactions with dependencies
    config_manager.get_endpoint_config.assert_called_once_with("customers", "get")
    execution_tracker.start_execution.assert_called_once_with("customers", "get", request_data)
    orchestrator.orchestrate.assert_called_once_with(
        "exec_123",
        config_manager.get_endpoint_config.return_value,
        request_data
    )
    response_assembler.assemble_response.assert_called_once_with(
        config_manager.get_endpoint_config.return_value,
        orchestrator.orchestrate.return_value,
        "exec_123"
    )
    execution_tracker.complete_execution.assert_called_once_with("exec_123", success=True)

@pytest.mark.asyncio
async def test_process_multiple_sources():
    """Test processing a request that combines data from multiple sources."""
    # Mock dependencies
    config_manager = MagicMock(spec=EndpointConfigManager)
    orchestrator = AsyncMock(spec=Orchestrator)
    execution_tracker = MagicMock(spec=ExecutionTracker)
    response_assembler = MagicMock(spec=ResponseAssembler)
    
    # Set up mock behaviors
    config_manager.get_endpoint_config.return_value = {
        "data_sources": [
            {
                "name": "customer_data",
                "type": "database",
                "operation": "get_customer",
                "params": {
                    "customer_id": "$request.customer_id"
                }
            },
            {
                "name": "customer_features",
                "type": "feast",
                "operation": "get_customer_features",
                "params": {
                    "customer_id": "$request.customer_id"
                }
            }
        ],
        "response_mapping": {
            "customer_id": "$customer_data.customer_id",
            "name": "$customer_data.name",
            "features": {
                "lifetime_value": "$customer_features.lifetime_value"
            }
        }
    }
    
    execution_tracker.start_execution.return_value = "exec_456"
    
    customer_data = {
        "customer_id": "cust_123",
        "name": "John Doe",
        "email": "john.doe@example.com"
    }
    
    customer_features = {
        "lifetime_value": 1500.75,
        "purchase_frequency": 2.3
    }
    
    orchestration_result = {
        "customer_data": customer_data,
        "customer_features": customer_features
    }
    
    orchestrator.orchestrate.return_value = orchestration_result
    
    expected_response = {
        "customer_id": "cust_123",
        "name": "John Doe",
        "features": {
            "lifetime_value": 1500.75
        }
    }
    
    response_assembler.assemble_response.return_value = expected_response
    
    # Create the request processor
    processor = RequestProcessor(
        config_manager=config_manager,
        orchestrator=orchestrator,
        execution_tracker=execution_tracker,
        response_assembler=response_assembler
    )
    
    # Process a request
    request_data = {"customer_id": "cust_123"}
    result = await processor.process("customers", "get_enriched", request_data)
    
    # Verify the result
    assert result == expected_response
    
    # Verify the interactions with dependencies
    config_manager.get_endpoint_config.assert_called_once_with("customers", "get_enriched")
    execution_tracker.start_execution.assert_called_once_with("customers", "get_enriched", request_data)
    orchestrator.orchestrate.assert_called_once_with(
        "exec_456",
        config_manager.get_endpoint_config.return_value,
        request_data
    )
    response_assembler.assemble_response.assert_called_once_with(
        config_manager.get_endpoint_config.return_value,
        orchestration_result,
        "exec_456"
    )
    execution_tracker.complete_execution.assert_called_once_with("exec_456", success=True)