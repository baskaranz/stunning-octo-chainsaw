from typing import Any, Dict, Optional
from fastapi import Depends

from app.config.endpoint_config_manager import EndpointConfigManager
from app.orchestration.orchestration_interfaces import Orchestrator
from app.orchestration.execution_tracker import ExecutionTracker
from app.orchestration.response_assembler import ResponseAssembler
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class RequestProcessor:
    """Processes incoming API requests by orchestrating data flows."""
    
    def __init__(
        self,
        config_manager: EndpointConfigManager = Depends(),
        orchestrator: Orchestrator = Depends(),
        execution_tracker: ExecutionTracker = Depends(),
        response_assembler: ResponseAssembler = Depends()
    ):
        self.config_manager = config_manager
        self.orchestrator = orchestrator
        self.execution_tracker = execution_tracker
        self.response_assembler = response_assembler
    
    async def process(self, domain: str, operation: str, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process an API request through the orchestration pipeline.
        
        Args:
            domain: The business domain (e.g., 'customers', 'orders')
            operation: The operation type (e.g., 'get', 'list', 'create')
            request_data: The incoming request data
            
        Returns:
            The assembled response or None if no data is found
        """
        # Get endpoint configuration for this domain/operation
        config = self.config_manager.get_endpoint_config(domain, operation)
        if not config:
            return None
        
        # Start tracking execution
        execution_id = self.execution_tracker.start_execution(domain, operation, request_data)
        
        try:
            # Orchestrate data retrieval/manipulation across sources
            data_result = await self.orchestrator.orchestrate(
                execution_id, 
                config,
                request_data
            )
            
            # Assemble the final response
            response = self.response_assembler.assemble_response(
                config,
                data_result,
                execution_id
            )
            
            # Mark execution as complete
            self.execution_tracker.complete_execution(execution_id, success=True)
            
            return response
            
        except Exception as e:
            # Mark execution as failed
            self.execution_tracker.complete_execution(execution_id, success=False, error=str(e))
            raise
            
    def process_request(self, endpoint_config: Dict[str, Any], parameters: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Process and validate request parameters for an endpoint.
        
        Args:
            endpoint_config: The endpoint configuration
            parameters: The request parameters
            execution_id: The unique execution ID
            
        Returns:
            The processed request data
        """
        # For now, just return the parameters as-is
        # Future: add parameter validation, type conversion, etc.
        return parameters
