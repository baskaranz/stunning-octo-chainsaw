from typing import Any, Dict, List, Optional
import json
from urllib.parse import urlencode

class ApiRequestBuilder:
    """Builds API requests for external services."""
    
    @staticmethod
    def build_url(base_url: str, path: str, query_params: Optional[Dict[str, Any]] = None) -> str:
        """Build a complete URL with query parameters.
        
        Args:
            base_url: The base URL
            path: The endpoint path
            query_params: Optional query parameters
            
        Returns:
            The complete URL
        """
        # Ensure base_url doesn't end with / and path starts with /
        base_url = base_url.rstrip("/")
        path = "/" + path.lstrip("/")
        
        url = base_url + path
        
        # Add query parameters if provided
        if query_params:
            query_string = urlencode(query_params)
            url = f"{url}?{query_string}"
        
        return url
    
    @staticmethod
    def build_headers(default_headers: Optional[Dict[str, str]] = None, 
                     additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers.
        
        Args:
            default_headers: Default headers to include
            additional_headers: Additional headers to add or override defaults
            
        Returns:
            The combined headers
        """
        headers = default_headers or {}
        
        # Add or override with additional headers
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    @staticmethod
    def build_request_body(data: Dict[str, Any], content_type: str = "application/json") -> tuple[str, Dict[str, str]]:
        """Build a request body with appropriate content type.
        
        Args:
            data: The data to include in the body
            content_type: The content type (default: application/json)
            
        Returns:
            Tuple of (body_content, headers)
        """
        headers = {"Content-Type": content_type}
        
        if content_type == "application/json":
            body = json.dumps(data)
        elif content_type == "application/x-www-form-urlencoded":
            body = urlencode(data)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
        
        return body, headers
    
    @staticmethod
    def parse_response(response_text: str, content_type: Optional[str] = None) -> Any:
        """Parse a response based on content type.
        
        Args:
            response_text: The response text
            content_type: The content type header
            
        Returns:
            The parsed response
        """
        if not response_text:
            return None
        
        if content_type and "application/json" in content_type:
            return json.loads(response_text)
        
        # Try to parse as JSON anyway if it looks like JSON
        if response_text.strip().startswith(("{" ,"[")):
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass
        
        # Return as text if can't parse as JSON
        return response_text
