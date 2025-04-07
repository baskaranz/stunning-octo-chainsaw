"""
Generic Orchestrator Controller

This module provides a generic orchestration API that handles requests for different
model scoring endpoints based on configuration. It allows for centralized orchestration
with endpoints like:
- /orchestrator/model_scoring/churn_pred
- /orchestrator/model_scoring/loan_pred

All model scoring logic is configuration-driven, allowing new models to be added
without code changes.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, Request
from typing import Dict, Any, Optional, List
import re

from app.orchestration.request_processor import RequestProcessor
from app.config.endpoint_config_manager import EndpointConfigManager

router = APIRouter()

# Regular expression to validate model names (only allow alphanumeric, dash and underscore)
MODEL_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

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
    if not MODEL_NAME_PATTERN.match(model_name):
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
    if not MODEL_NAME_PATTERN.match(model_name):
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