"""Interfaces for orchestration components to avoid circular dependencies."""
from typing import Any, Dict, Optional, Protocol


class ConfigProvider(Protocol):
    """Interface for components that provide configuration."""
    
    def get_endpoint_config(self, endpoint_id: str, domain: Optional[str] = None, 
                           version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get endpoint configuration."""
        ...


class RequestPreprocessor(Protocol):
    """Interface for components that preprocess requests."""
    
    def process_request(self, endpoint_config: Dict[str, Any], 
                        parameters: Dict[str, Any], 
                        execution_id: str) -> Dict[str, Any]:
        """Process and validate a request before orchestration."""
        ...


class ResponsePostprocessor(Protocol):
    """Interface for components that postprocess responses."""
    
    def assemble_response(self, endpoint_config: Dict[str, Any], 
                         data_result: Dict[str, Any],
                         execution_id: Optional[str] = None) -> Dict[str, Any]:
        """Assemble the final response after orchestration."""
        ...


class Orchestrator(Protocol):
    """Interface for components that orchestrate data flow."""
    
    async def orchestrate(self, execution_id: str, 
                         endpoint_config: Dict[str, Any],
                         request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate data flow across multiple sources."""
        ...