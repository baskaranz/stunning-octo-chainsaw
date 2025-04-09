"""
Generic Orchestrator Controller

This module provides a generic orchestration API that handles requests for different
domains based on configuration. It allows for centralized orchestration with endpoints like:
- /orchestrator/model_scoring/churn_pred
- /orchestrator/model_scoring/loan_pred
- /orchestrator/iris_example/predict/{flower_id}

All orchestration logic is configuration-driven, allowing new domains to be added
without code changes.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, Request
from typing import Dict, Any, Optional, List
import re

from app.orchestration.request_processor import RequestProcessor
from app.config.endpoint_config_manager import EndpointConfigManager

router = APIRouter()

# Regular expression to validate domain and operation names (only allow alphanumeric, dash and underscore)
VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

@router.get("/model_scoring/{model_name}/{entity_id}")
async def get_model_scoring_with_id(
    request: Request,
    model_name: str = Path(..., description="The name of the model to use for scoring"),
    entity_id: str = Path(..., description="The ID of the entity to score (e.g., customer_id)"),
    request_processor: RequestProcessor = Depends(),
    endpoint_config: EndpointConfigManager = Depends()
):
    """
    Generic model scoring endpoint with entity ID in path.
    
    This endpoint allows providing an entity ID (like customer_id) directly in the path.
    
    Args:
        model_name: The name of the model to use (e.g., 'credit_risk', 'loan_pred')
        entity_id: The ID of the entity to score (e.g., customer_id)
        request: The incoming FastAPI request object
    
    Returns:
        The model prediction with additional context based on the model's configuration
    """
    # Validate model name to prevent injection attacks
    if not VALID_NAME_PATTERN.match(model_name):
        raise HTTPException(status_code=400, detail="Invalid model name format")
    
    # Use model_name as the domain and 'predict' as the operation
    domain = f"model_scoring_{model_name}"
    operation = "predict"
    
    # Check if the domain/operation exists in config
    config = endpoint_config.get_endpoint_config(domain, operation)
    if not config:
        raise HTTPException(
            status_code=404, 
            detail=f"Model scoring configuration not found for model: {model_name}"
        )
    
    # Extract query parameters
    query_params = dict(request.query_params)
    
    # Process the request through the orchestrator
    result = await request_processor.process(
        domain=domain,
        operation=operation,
        request_data={
            "path_params": {"model_name": model_name, "entity_id": entity_id},
            "query_params": query_params,
            "body": {}
        }
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to get prediction for model: {model_name} and entity: {entity_id}"
        )
    
    return result

@router.get("/model_scoring/{model_name}")
async def get_model_scoring(
    request: Request,
    model_name: str = Path(..., description="The name of the model to use for scoring"),
    request_processor: RequestProcessor = Depends(),
    endpoint_config: EndpointConfigManager = Depends()
):
    """
    Generic model scoring endpoint.
    
    This endpoint orchestrates data collection from different sources (database, feature store, etc.)
    based on the model configuration, then sends the data to the appropriate ML model for scoring.
    
    All orchestration logic is configuration-driven, making it easy to add new models without code changes.
    
    Args:
        model_name: The name of the model to use (e.g., 'churn_pred', 'loan_pred')
        request: The incoming FastAPI request object
    
    Returns:
        The model prediction with additional context based on the model's configuration
    """
    # Validate model name to prevent injection attacks
    if not VALID_NAME_PATTERN.match(model_name):
        raise HTTPException(status_code=400, detail="Invalid model name format")
    
    # Use model_name as the domain and 'predict' as the operation
    domain = f"model_scoring_{model_name}"
    operation = "predict"
    
    # Check if the domain/operation exists in config
    config = endpoint_config.get_endpoint_config(domain, operation)
    if not config:
        raise HTTPException(
            status_code=404, 
            detail=f"Model scoring configuration not found for model: {model_name}"
        )
    
    # Extract query parameters
    query_params = dict(request.query_params)
    
    # Process the request through the orchestrator
    result = await request_processor.process(
        domain=domain,
        operation=operation,
        request_data={
            "path_params": {"model_name": model_name},
            "query_params": query_params,
            "body": {}
        }
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to get prediction for model: {model_name}"
        )
    
    return result

@router.post("/model_scoring/{model_name}")
async def post_model_scoring(
    request: Request,
    model_name: str = Path(..., description="The name of the model to use for scoring"),
    body: Dict[str, Any] = Body(..., description="Additional features or parameters for the model"),
    request_processor: RequestProcessor = Depends(),
    endpoint_config: EndpointConfigManager = Depends()
):
    """
    Generic model scoring endpoint with request body.
    
    Similar to the GET endpoint, but allows sending additional features or parameters in the request body.
    This is useful for more complex model inputs or when the feature set is dynamic.
    
    Args:
        model_name: The name of the model to use (e.g., 'churn_pred', 'loan_pred')
        body: Additional features or parameters for the model
        request: The incoming FastAPI request object
    
    Returns:
        The model prediction with additional context based on the model's configuration
    """
    # Validate model name to prevent injection attacks
    if not VALID_NAME_PATTERN.match(model_name):
        raise HTTPException(status_code=400, detail="Invalid model name format")
    
    # Use model_name as the domain and 'predict' as the operation
    domain = f"model_scoring_{model_name}"
    operation = "predict"
    
    # Check if the domain/operation exists in config
    config = endpoint_config.get_endpoint_config(domain, operation)
    if not config:
        raise HTTPException(
            status_code=404, 
            detail=f"Model scoring configuration not found for model: {model_name}"
        )
    
    # Extract query parameters
    query_params = dict(request.query_params)
    
    # Process the request through the orchestrator
    result = await request_processor.process(
        domain=domain,
        operation=operation,
        request_data={
            "path_params": {"model_name": model_name},
            "query_params": query_params,
            "body": body
        }
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to get prediction for model: {model_name}"
        )
    
    return result

@router.get("/domains")
async def list_domains(
    endpoint_config: EndpointConfigManager = Depends()
):
    """
    List all available domains.
    
    Returns a list of all configured domains.
    
    Returns:
        A list of available domain names
    """
    # Get all domains from config_loader
    all_domains = endpoint_config.config_loader.list_domain_configs()
    return all_domains

@router.get("/model_scoring")
async def list_available_models(
    endpoint_config: EndpointConfigManager = Depends()
):
    """
    List all available model scoring endpoints.
    
    Returns information about all configured model scoring endpoints including their
    descriptions, input requirements, and output formats.
    
    Returns:
        A list of available model scoring endpoints with metadata
    """
    # Get all domains that start with 'model_scoring_'
    available_models = []
    
    # Use a list of all domains from config_loader
    all_domains = endpoint_config.config_loader.list_domain_configs()
    
    for domain in all_domains:
        # Check if domain starts with model_scoring_
        if domain.startswith("model_scoring_"):
            model_name = domain.replace("model_scoring_", "")
            
            # Get domain config
            domain_config = endpoint_config.config_loader.load_domain_config(domain)
            if domain_config:
                # Extract relevant information
                description = domain_config.get("description", "")
                endpoints = domain_config.get("endpoints", {})
                
                # Get prediction endpoint config
                predict_endpoint = endpoints.get("predict", {})
                input_schema = predict_endpoint.get("input_schema", {})
                output_schema = predict_endpoint.get("output_schema", {})
                
                available_models.append({
                    "model_name": model_name,
                    "description": description,
                    "input_schema": input_schema,
                    "output_schema": output_schema,
                    "endpoint": f"/orchestrator/model_scoring/{model_name}"
                })
    
    if not available_models:
        return {"models": [], "message": "No model scoring endpoints configured"}
    
    return {"models": available_models}
    
@router.get("/{domain}/{operation}/{entity_id}")
async def generic_domain_operation_with_id(
    request: Request,
    domain: str = Path(..., description="The domain name"),
    operation: str = Path(..., description="The operation to perform"),
    entity_id: str = Path(..., description="The ID of the entity to process"),
    request_processor: RequestProcessor = Depends(),
    endpoint_config: EndpointConfigManager = Depends()
):
    """
    Generic domain operation endpoint with entity ID in path.
    
    This endpoint handles any domain operation with an entity ID in the path.
    
    Args:
        domain: The domain name (e.g., 'iris_example', 'customers')
        operation: The operation to perform (e.g., 'predict', 'samples')
        entity_id: The ID of the entity to process
        request: The incoming FastAPI request object
    
    Returns:
        The response based on the domain operation configuration
    """
    # Validate domain and operation names to prevent injection attacks
    if not VALID_NAME_PATTERN.match(domain) or not VALID_NAME_PATTERN.match(operation):
        raise HTTPException(status_code=400, detail="Invalid domain or operation format")
    
    # Special case handling for model_scoring domain
    if domain == "model_scoring":
        return await get_model_scoring_with_id(request, operation, entity_id, request_processor, endpoint_config)
    
    # Check if the domain/operation exists in config
    config = endpoint_config.get_endpoint_config(domain, operation)
    if not config:
        raise HTTPException(
            status_code=404, 
            detail=f"Configuration not found for domain: {domain}, operation: {operation}"
        )
    
    # Extract query parameters
    query_params = dict(request.query_params)
    
    # Process the request through the orchestrator
    result = await request_processor.process(
        domain=domain,
        operation=operation,
        request_data={
            "path_params": {"domain": domain, "operation": operation, "entity_id": entity_id},
            "query_params": query_params,
            "body": {}
        }
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to process request for domain: {domain}, operation: {operation}, entity: {entity_id}"
        )
    
    return result

@router.get("/{domain}/{operation}")
async def generic_domain_operation(
    request: Request,
    domain: str = Path(..., description="The domain name"),
    operation: str = Path(..., description="The operation to perform"),
    request_processor: RequestProcessor = Depends(),
    endpoint_config: EndpointConfigManager = Depends()
):
    """
    Generic domain operation endpoint.
    
    This endpoint handles any domain operation without an entity ID.
    
    Args:
        domain: The domain name (e.g., 'iris_example', 'customers')
        operation: The operation to perform (e.g., 'samples', 'list')
        request: The incoming FastAPI request object
    
    Returns:
        The response based on the domain operation configuration
    """
    # Validate domain and operation names to prevent injection attacks
    if not VALID_NAME_PATTERN.match(domain) or not VALID_NAME_PATTERN.match(operation):
        raise HTTPException(status_code=400, detail="Invalid domain or operation format")
    
    # Special case handling for model_scoring domain
    if domain == "model_scoring":
        return await get_model_scoring(request, operation, request_processor, endpoint_config)
    
    # Check if the domain/operation exists in config
    config = endpoint_config.get_endpoint_config(domain, operation)
    if not config:
        raise HTTPException(
            status_code=404, 
            detail=f"Configuration not found for domain: {domain}, operation: {operation}"
        )
    
    # Extract query parameters
    query_params = dict(request.query_params)
    
    # Process the request through the orchestrator
    result = await request_processor.process(
        domain=domain,
        operation=operation,
        request_data={
            "path_params": {"domain": domain, "operation": operation},
            "query_params": query_params,
            "body": {}
        }
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to process request for domain: {domain}, operation: {operation}"
        )
    
    return result
    
@router.post("/{domain}/{operation}")
async def post_generic_domain_operation(
    request: Request,
    domain: str = Path(..., description="The domain name"),
    operation: str = Path(..., description="The operation to perform"),
    body: Dict[str, Any] = Body(..., description="Request body"),
    request_processor: RequestProcessor = Depends(),
    endpoint_config: EndpointConfigManager = Depends()
):
    """
    Generic domain operation endpoint with POST method.
    
    This endpoint handles any domain operation with a request body.
    
    Args:
        domain: The domain name (e.g., 'iris_example', 'customers')
        operation: The operation to perform (e.g., 'predict', 'create')
        body: Request body with additional parameters
        request: The incoming FastAPI request object
    
    Returns:
        The response based on the domain operation configuration
    """
    # Validate domain and operation names to prevent injection attacks
    if not VALID_NAME_PATTERN.match(domain) or not VALID_NAME_PATTERN.match(operation):
        raise HTTPException(status_code=400, detail="Invalid domain or operation format")
    
    # Special case handling for model_scoring domain
    if domain == "model_scoring":
        return await post_model_scoring(request, operation, body, request_processor, endpoint_config)
    
    # Check if the domain/operation exists in config
    config = endpoint_config.get_endpoint_config(domain, operation)
    if not config:
        raise HTTPException(
            status_code=404, 
            detail=f"Configuration not found for domain: {domain}, operation: {operation}"
        )
    
    # Extract query parameters
    query_params = dict(request.query_params)
    
    # Process the request through the orchestrator
    result = await request_processor.process(
        domain=domain,
        operation=operation,
        request_data={
            "path_params": {"domain": domain, "operation": operation},
            "query_params": query_params,
            "body": body
        }
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to process request for domain: {domain}, operation: {operation}"
        )
    
    return result

@router.post("/{domain}/{operation}/{entity_id}")
async def post_generic_domain_operation_with_id(
    request: Request,
    domain: str = Path(..., description="The domain name"),
    operation: str = Path(..., description="The operation to perform"),
    entity_id: str = Path(..., description="The ID of the entity to process"),
    body: Dict[str, Any] = Body(..., description="Request body"),
    request_processor: RequestProcessor = Depends(),
    endpoint_config: EndpointConfigManager = Depends()
):
    """
    Generic domain operation endpoint with entity ID and POST method.
    
    This endpoint handles any domain operation with a request body and an entity ID.
    
    Args:
        domain: The domain name (e.g., 'iris_example', 'customers')
        operation: The operation to perform (e.g., 'predict', 'update')
        entity_id: The ID of the entity to process
        body: Request body with additional parameters
        request: The incoming FastAPI request object
    
    Returns:
        The response based on the domain operation configuration
    """
    # Validate domain and operation names to prevent injection attacks
    if not VALID_NAME_PATTERN.match(domain) or not VALID_NAME_PATTERN.match(operation):
        raise HTTPException(status_code=400, detail="Invalid domain or operation format")
    
    # Special case handling for model_scoring domain
    if domain == "model_scoring":
        # For now, we don't have a POST with ID handler for model_scoring
        # This would need to be implemented if needed
        raise HTTPException(
            status_code=404,
            detail=f"POST with entity ID not supported for model_scoring domain"
        )
    
    # Check if the domain/operation exists in config
    config = endpoint_config.get_endpoint_config(domain, operation)
    if not config:
        raise HTTPException(
            status_code=404, 
            detail=f"Configuration not found for domain: {domain}, operation: {operation}"
        )
    
    # Extract query parameters
    query_params = dict(request.query_params)
    
    # Process the request through the orchestrator
    result = await request_processor.process(
        domain=domain,
        operation=operation,
        request_data={
            "path_params": {"domain": domain, "operation": operation, "entity_id": entity_id},
            "query_params": query_params,
            "body": body
        }
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Failed to process request for domain: {domain}, operation: {operation}, entity: {entity_id}"
        )
    
    return result