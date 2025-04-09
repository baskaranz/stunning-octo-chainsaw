from typing import Any, Dict, List, Optional
from fastapi import Depends
import httpx
import json

from app.config.data_source_config_manager import DataSourceConfigManager
from app.common.errors.custom_exceptions import ApiError
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class HttpClient:
    """Client for external API operations."""
    
    def __init__(self, config_manager: DataSourceConfigManager = Depends()):
        self.config_manager = config_manager
        self.clients = {}
    
    def _get_client(self, source_id: str):
        """Get an HTTP client for the specified source ID."""
        if source_id in self.clients:
            return self.clients[source_id]
        
        # Get the API configuration
        config = self.config_manager.get_data_source_config("api", source_id)
        if not config:
            raise ApiError(f"API configuration not found for source '{source_id}'", source_id)
        
        # Create the client
        try:
            base_url = config.get("base_url")
            if not base_url:
                raise ApiError(f"Missing base URL for API source '{source_id}'", source_id)
            
            # Get default headers and timeout
            headers = config.get("headers", {})
            timeout = config.get("timeout", 30.0)
            
            # Debug information
            logger.info(f"Creating HTTP client for {source_id} with base_url: {base_url}")
            
            # Verify is set to False to accept self-signed certificates
            # This is for development/example purposes only, not recommended for production
            client = httpx.AsyncClient(
                base_url=base_url, 
                headers=headers, 
                timeout=timeout,
                follow_redirects=True
            )
            self.clients[source_id] = client
            return client
        except Exception as e:
            logger.error(f"Error creating HTTP client for source '{source_id}': {str(e)}")
            raise ApiError(f"Error initializing API client: {str(e)}", source_id)
    
    async def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, 
                     data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, 
                     source_id: str = "default", domain: Optional[str] = None, direct_url: bool = False) -> Dict[str, Any]:
        """Make an HTTP request to the external API.
        
        Args:
            method: The HTTP method (GET, POST, etc.)
            path: The API endpoint path or full URL if direct_url=True
            params: Query parameters
            data: Request body data
            headers: Additional headers
            source_id: The API source ID
            domain: Optional domain for domain-specific configurations
            direct_url: If True, path is treated as a complete URL instead of a path
            
        Returns:
            The response data
        """
        if direct_url:
            # Create a one-time client for the direct URL request
            custom_headers = headers or {}
            timeout = 30.0  # Default timeout for direct requests
            
            try:
                logger.info(f"Making direct {method} request to {path}")
                async with httpx.AsyncClient(
                    headers=custom_headers, 
                    timeout=timeout,
                    follow_redirects=True
                ) as client:
                    # Prepare request
                    request_args = {
                        "method": method,
                        "url": path,
                    }
                    
                    if params:
                        request_args["params"] = params
                    
                    if data:
                        request_args["json"] = data
                    
                    response = await client.request(**request_args)
                    
                    # Check for error status codes
                    response.raise_for_status()
                    
                    # Parse response
                    if response.headers.get("content-type", "").startswith("application/json"):
                        return response.json()
                    else:
                        return {"content": response.text, "status_code": response.status_code}
            except httpx.HTTPStatusError as e:
                # Handle HTTP error responses
                error_message = f"HTTP error {e.response.status_code}"
                
                # Try to parse error response
                try:
                    error_data = e.response.json()
                    if isinstance(error_data, dict) and "message" in error_data:
                        error_message = error_data["message"]
                except Exception:
                    pass
                
                logger.error(f"API error for direct URL request: {error_message}")
                raise ApiError(error_message, "direct_request", e.response.status_code)
            except Exception as e:
                logger.error(f"Error making direct URL request: {str(e)}")
                raise ApiError(f"Direct URL request failed: {str(e)}", "direct_request")
        else:
            # Get or create a client for the API source
            config = self.config_manager.get_data_source_config("api", source_id, domain)
            if not config:
                raise ApiError(f"API configuration not found for source '{source_id}'", source_id)
            
            client = self._get_client(source_id)
            
            # Prepare request
            request_args = {
                "method": method,
                "url": path,
            }
            
            if params:
                request_args["params"] = params
            
            if data:
                request_args["json"] = data
            
            if headers:
                request_args["headers"] = headers
            
            try:
                logger.info(f"Making {method} request to {path} on API source '{source_id}'")
                response = await client.request(**request_args)
                
                # Check for error status codes
                response.raise_for_status()
                
                # Parse response
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                else:
                    return {"content": response.text, "status_code": response.status_code}
                
            except httpx.HTTPStatusError as e:
                # Handle HTTP error responses
                error_message = f"HTTP error {e.response.status_code}"
                
                # Try to parse error response
                try:
                    error_data = e.response.json()
                    if isinstance(error_data, dict) and "message" in error_data:
                        error_message = error_data["message"]
                except Exception:
                    pass
                
                logger.error(f"API error from source '{source_id}': {error_message}")
                raise ApiError(error_message, source_id, e.response.status_code)
                
            except httpx.RequestError as e:
                # Handle request exceptions (network errors, timeouts, etc.)
                logger.error(f"Request error for API source '{source_id}': {str(e)}")
                raise ApiError(f"Request failed: {str(e)}", source_id)
                
            except Exception as e:
                # Handle any other exceptions
                logger.error(f"Unexpected error for API source '{source_id}': {str(e)}")
                raise ApiError(f"Unexpected error: {str(e)}", source_id)
    
    # Convenience methods for common HTTP methods
    
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, 
                 headers: Optional[Dict[str, str]] = None, source_id: str = "default", 
                 domain: Optional[str] = None, direct_url: bool = False) -> Dict[str, Any]:
        """Make a GET request."""
        return await self.request("GET", path, params=params, headers=headers, 
                                source_id=source_id, domain=domain, direct_url=direct_url)
    
    async def post(self, path: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None, 
                  headers: Optional[Dict[str, str]] = None, source_id: str = "default",
                  domain: Optional[str] = None, direct_url: bool = False) -> Dict[str, Any]:
        """Make a POST request."""
        return await self.request("POST", path, params=params, data=data, headers=headers, 
                                source_id=source_id, domain=domain, direct_url=direct_url)
    
    async def put(self, path: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None, 
                 headers: Optional[Dict[str, str]] = None, source_id: str = "default",
                 domain: Optional[str] = None, direct_url: bool = False) -> Dict[str, Any]:
        """Make a PUT request."""
        return await self.request("PUT", path, params=params, data=data, headers=headers, 
                                source_id=source_id, domain=domain, direct_url=direct_url)
    
    async def delete(self, path: str, params: Optional[Dict[str, Any]] = None, 
                    headers: Optional[Dict[str, str]] = None, source_id: str = "default",
                    domain: Optional[str] = None, direct_url: bool = False) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self.request("DELETE", path, params=params, headers=headers, 
                                source_id=source_id, domain=domain, direct_url=direct_url)
    
    # Example operations for external API integration
    
    async def get_customer_credit_score(self, customer_id: str, source_id: str = "credit_api") -> Dict[str, Any]:
        """Get a customer's credit score from an external API.
        
        Args:
            customer_id: The customer ID
            source_id: The API source ID
            
        Returns:
            Credit score data
        """
        try:
            return await self.get(f"/customers/{customer_id}/credit-score", source_id=source_id)
        except Exception as e:
            logger.error(f"Error fetching credit score for customer {customer_id}: {str(e)}")
            raise ApiError(f"Failed to retrieve credit score: {str(e)}", source_id)
