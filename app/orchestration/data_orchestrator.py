from typing import Any, Dict, List, Optional
from fastapi import Depends

from app.adapters.database.database_client import DatabaseClient
from app.adapters.api.http_client import HttpClient
from app.adapters.feast.feast_client import FeastClient
from app.adapters.ml.model_client import ModelClient
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class DataOrchestrator:
    """Orchestrates data flow between different data sources."""
    
    def __init__(
        self,
        database: DatabaseClient = Depends(),
        http_client: HttpClient = Depends(),
        feast_client: FeastClient = Depends(),
        model_client: ModelClient = Depends()
    ):
        self.sources = {
            "database": database,
            "api": http_client,
            "feast": feast_client,
            "ml": model_client
        }
    
    async def orchestrate(
        self, 
        execution_id: str, 
        endpoint_config: Dict[str, Any], 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Orchestrate data flow across multiple sources.
        
        Args:
            execution_id: The unique execution ID for tracking
            endpoint_config: The endpoint configuration
            request_data: The original request data
            
        Returns:
            The combined data result from all sources
        """
        result = {}
        
        # Check if endpoint has an explicit type
        endpoint_type = endpoint_config.get("endpoint_type")
        
        # Get the data sources defined in the endpoint configuration
        sources = endpoint_config.get("data_sources", [])
        
        # Validate that sources match the endpoint type (if specified)
        if endpoint_type and endpoint_type != "composite":
            # Filter sources to only include those matching the endpoint type
            matching_sources = [s for s in sources if s.get("type") == endpoint_type]
            
            if not matching_sources and sources:
                logger.warning(
                    f"Endpoint type '{endpoint_type}' specified, but no matching data sources found. "
                    f"This may lead to unexpected results for execution {execution_id}"
                )
            
            # Use only the matching sources
            sources = matching_sources
        
        for source in sources:
            source_type = source.get("type")
            source_name = source.get("name")
            operation = source.get("operation")
            params = source.get("params", {})
            transform = source.get("transform", None)
            
            # Skip if missing required configuration
            if not all([source_type, source_name, operation]):
                logger.warning(f"Skipping misconfigured source in execution {execution_id}")
                continue
                
            # Check if this source has a condition
            condition = source.get("condition")
            if condition:
                # Simple condition evaluation - only supports references to request and result
                try:
                    # Evaluate the condition (very simple evaluation for now)
                    if condition.startswith("$"):
                        parts = condition[1:].split(".")
                        
                        # Get value from request or previous results
                        if parts[0] == "request":
                            value = self._get_nested_value(request_data, parts[1:])
                        elif parts[0] in result:
                            value = self._get_nested_value(result[parts[0]], parts[1:])
                        else:
                            value = None
                            
                        # Skip if condition evaluates to false/None
                        if not value:
                            logger.info(f"Skipping source '{source_name}' in execution {execution_id} due to condition: {condition}")
                            continue
                    else:
                        # For more complex conditions, we might need a proper expression evaluator
                        # For now, just log and continue with execution
                        logger.warning(f"Complex condition not supported: {condition} in execution {execution_id}")
                except Exception as e:
                    logger.warning(f"Error evaluating condition '{condition}' in execution {execution_id}: {str(e)}")
                    # Continue with execution as fallback
            
            try:
                # Resolve parameter values from request data
                resolved_params = self._resolve_params(params, request_data, result)
                
                # Check if this is a direct mapping - special case for using request data directly
                if source_type == "direct":
                    # Just use the parameters directly without calling any external source
                    source_result = resolved_params
                    result[source_name] = source_result
                    continue
                    
                # Skip if the source type is not supported
                if source_type not in self.sources:
                    logger.warning(f"Unsupported source type '{source_type}' in execution {execution_id}")
                    continue
                
                # Execute the operation on the data source
                source_result = await self._execute_source_operation(
                    source_type, 
                    operation, 
                    resolved_params
                )
                
                # Apply transform if specified
                if transform and source_result:
                    source_result = self._apply_transform(transform, source_result, result)
                
                # Add the result to the combined result
                result[source_name] = source_result
                
            except Exception as e:
                logger.error(f"Error executing source '{source_name}' in execution {execution_id}: {str(e)}")
                raise
        
        return result
    
    def _resolve_params(self, params: Dict[str, Any], request_data: Dict[str, Any], current_result: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter values from request data and earlier results."""
        resolved = {}
        
        for param_name, param_value in params.items():
            # If the parameter value is a reference to request data or previous result
            if isinstance(param_value, str) and param_value.startswith("$"):
                path = param_value[1:].split(".")
                
                if path[0] == "request":
                    # Get from request data
                    value = self._get_nested_value(request_data, path[1:])
                elif path[0] in current_result:
                    # Get from a previous source result
                    value = self._get_nested_value(current_result[path[0]], path[1:])
                else:
                    # Default to None if not found
                    value = None
                
                resolved[param_name] = value
            else:
                # Use the literal value
                resolved[param_name] = param_value
        
        return resolved
    
    def _get_nested_value(self, data: Dict[str, Any], path: List[str]) -> Any:
        """Get a value from nested dictionaries using a path."""
        current = data
        
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    async def _execute_source_operation(self, source_type: str, operation: str, params: Dict[str, Any]) -> Any:
        """Execute an operation on a data source."""
        source = self.sources[source_type]
        
        # Call the operation method on the source client
        if hasattr(source, operation) and callable(getattr(source, operation)):
            return await getattr(source, operation)(**params)
        else:
            raise ValueError(f"Operation '{operation}' not supported by source type '{source_type}'")
    
    def _apply_transform(self, transform: Dict[str, Any], source_result: Any, current_result: Dict[str, Any]) -> Any:
        """Apply a transformation to the source result."""
        transform_type = transform.get("type")
        
        if transform_type == "select_fields":
            fields = transform.get("fields", [])
            if isinstance(source_result, dict):
                return {k: v for k, v in source_result.items() if k in fields}
            elif isinstance(source_result, list) and all(isinstance(item, dict) for item in source_result):
                return [{k: v for k, v in item.items() if k in fields} for item in source_result]
        
        # Return unchanged if no transformation applied
        return source_result