import pytest
import asyncio
from unittest.mock import MagicMock

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def request_preprocessor():
    """Create a mock request preprocessor for testing."""
    mock = MagicMock()
    
    # Add a process_request method that returns the parameters
    mock.process_request.side_effect = lambda config, params, execution_id=None: params
    
    # Add config_manager attribute
    mock.config_manager = MagicMock()
    mock.config_manager.get_endpoint_config.return_value = {}
    
    return mock

@pytest.fixture
def response_postprocessor():
    """Create a mock response postprocessor for testing."""
    mock = MagicMock()
    
    # Make assemble_response simply return the data_result
    mock.assemble_response.side_effect = lambda config, data, execution_id=None: data
    
    return mock

@pytest.fixture
def config_provider():
    """Create a mock config provider for testing."""
    mock = MagicMock()
    mock.get_endpoint_config.return_value = {}
    return mock