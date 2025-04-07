from typing import Any, Dict, Optional
import re
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ResponseAssembler:
    """Assembles the final response from orchestration results."""
    
    def assemble_response(
        self, 
        execution_id: str, 
        endpoint_config: Dict[str, Any], 
        data_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Assemble the final response from the orchestration results.
        
        Args:
            execution_id: The unique execution ID
            endpoint_config: The endpoint configuration
            data_result: The data result from orchestration
            
        Returns:
            The assembled response or None if no data available
        """
        # Get the response mapping from the endpoint configuration
        response_mapping = endpoint_config.get("response_mapping", {})
        
        # If no mapping is defined, return the primary data source result
        if not response_mapping:
            primary_source = endpoint_config.get("primary_source")
            if primary_source and primary_source in data_result:
                return data_result[primary_source]
            return None
        
        # Apply the response mapping to create the final response
        return self._map_response(response_mapping, data_result)
    
    def _map_response(self, mapping: Dict[str, Any], data_result: Dict[str, Any]) -> Dict[str, Any]:
        """Map data from multiple sources into a single response structure.
        
        Args:
            mapping: The response mapping configuration
            data_result: The data result from orchestration
            
        Returns:
            The mapped response
        """
        response = {}
        
        for target_field, source_ref in mapping.items():
            # Handle nested mappings recursively
            if isinstance(source_ref, dict):
                response[target_field] = self._map_response(source_ref, data_result)
                continue
                
            # Skip if not a string reference
            if not isinstance(source_ref, str):
                continue
                
            # Check for fallback/conditional expression with || operator
            if "||" in source_ref:
                # Split by the || operator and evaluate each part
                alternatives = source_ref.split("||")
                value = None
                
                for alt in alternatives:
                    alt = alt.strip()
                    
                    # Handle direct values (not references)
                    if alt.startswith('"') and alt.endswith('"'):
                        # String literal
                        value = alt[1:-1]
                        break
                    elif alt.isdigit():
                        # Integer literal
                        value = int(alt)
                        break
                    elif alt == "true":
                        value = True
                        break
                    elif alt == "false":
                        value = False
                        break
                    elif alt == "null":
                        value = None
                        break
                    elif re.match(r"^[-+]?[0-9]*\.?[0-9]+$", alt):
                        # Float literal
                        value = float(alt)
                        break
                    elif alt.startswith("$"):
                        # Parse the reference path
                        parts = alt[1:].split(".")
                        source_name = parts[0]
                        
                        # Skip to next alternative if source doesn't exist
                        if source_name not in data_result:
                            continue
                        
                        # Get the value from the source
                        if len(parts) > 1:
                            source_value = self._get_nested_value(data_result[source_name], parts[1:])
                        else:
                            source_value = data_result[source_name]
                        
                        # Use this value if it's not None or empty
                        if source_value is not None and (not isinstance(source_value, (str, list, dict)) or len(source_value) > 0):
                            value = source_value
                            break
                
                # Set the value in the response (which might be None if no alternatives matched)
                response[target_field] = value
                
            # Simple field reference
            elif source_ref.startswith("$"):
                parts = source_ref[1:].split(".")
                source_name = parts[0]
                
                # Skip if the source is not in the data result
                if source_name not in data_result:
                    continue
                
                # Get the value from the source
                if len(parts) > 1:
                    value = self._get_nested_value(data_result[source_name], parts[1:])
                else:
                    value = data_result[source_name]
                
                response[target_field] = value
        
        return response
    
    def _get_nested_value(self, data: Any, path: list) -> Any:
        """Get a value from nested data structures using a path."""
        current = data
        
        for key in path:
            # Handle list indexing
            if isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            # Handle dictionary access
            elif isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current