from typing import Any, Dict, Optional
import re
from app.common.utils.logging_utils import get_logger
from app.orchestration.orchestration_interfaces import ResponsePostprocessor

logger = get_logger(__name__)

class ResponseAssembler(ResponsePostprocessor):
    """Assembles the final response from orchestration results."""
    
    def assemble_response(
        self, 
        endpoint_config: Dict[str, Any], 
        data_result: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assemble the final response from the orchestration results.
        
        Args:
            endpoint_config: The endpoint configuration
            data_result: The data result from orchestration
            execution_id: Optional unique execution ID
            
        Returns:
            The assembled response
        """
        # Get the response template from the endpoint configuration
        response_template = endpoint_config.get("response_template", {})
        
        # If no template is defined, return the raw data result
        if not response_template:
            return data_result
        
        # Apply template substitution
        return self._apply_template(response_template, data_result)
    
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

    def _apply_template(self, template: Any, data_result: Dict[str, Any]) -> Any:
        """Apply template substitution to create the response.
        
        Args:
            template: The response template (can be dict, list, or string)
            data_result: The data result from orchestration
            
        Returns:
            The templated response
        """
        # Handle different template types
        if isinstance(template, dict):
            # Process each key in the dictionary template
            result = {}
            for key, value in template.items():
                result[key] = self._apply_template(value, data_result)
            return result
        
        elif isinstance(template, list):
            # Process each item in the list template
            result = []
            for item in template:
                result.append(self._apply_template(item, data_result))
            return result
        
        elif isinstance(template, str):
            # Check if this is a template variable reference like {source_name}
            if template.startswith("{") and template.endswith("}"):
                # Extract the variable name
                var_name = template[1:-1]
                
                # Check for nested references (e.g., {customer.name})
                if "." in var_name:
                    parts = var_name.split(".")
                    source_name = parts[0]
                    
                    # If the source exists in the data result
                    if source_name in data_result:
                        # Get nested value using the remaining path
                        return self._get_nested_value(data_result[source_name], parts[1:])
                    return None
                
                # Simple reference to a top-level source
                if var_name in data_result:
                    return data_result[var_name]
                return None
            
            # Check for embedded template variables like "Hello {customer.name}!"
            if "{" in template and "}" in template:
                result = template
                # Find all {variable} patterns
                pattern = r"\{([^}]+)\}"
                matches = re.findall(pattern, template)
                
                for match in matches:
                    placeholder = "{" + match + "}"
                    
                    # Handle nested references
                    if "." in match:
                        parts = match.split(".")
                        source_name = parts[0]
                        
                        if source_name in data_result:
                            value = self._get_nested_value(data_result[source_name], parts[1:])
                            # Replace the placeholder with the value (convert to string)
                            if value is not None:
                                result = result.replace(placeholder, str(value))
                    else:
                        # Simple reference
                        if match in data_result:
                            value = data_result[match]
                            if value is not None:
                                result = result.replace(placeholder, str(value))
                
                return result
            
            # Not a template, return as is
            return template
        
        # For other types (int, bool, etc.), return as is
        return template