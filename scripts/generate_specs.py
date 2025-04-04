#!/usr/bin/env python3

import os
import sys
import json
import yaml
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

def generate_openapi_spec():
    """Generate OpenAPI specification from the FastAPI app."""
    print("Generating OpenAPI specification...")
    
    # Create the FastAPI app
    app = create_app()
    
    # Get the OpenAPI JSON
    openapi_spec = app.openapi()
    
    # Create the api_spec directory if it doesn't exist
    api_spec_dir = Path('api_spec')
    api_spec_dir.mkdir(exist_ok=True)
    
    # Save as JSON
    with open(api_spec_dir / 'openapi.json', 'w') as f:
        json.dump(openapi_spec, f, indent=2)
    
    # Save as YAML
    with open(api_spec_dir / 'openapi.yaml', 'w') as f:
        yaml.dump(openapi_spec, f, sort_keys=False)
    
    print(f"OpenAPI specification saved to {api_spec_dir}/openapi.json and {api_spec_dir}/openapi.yaml")

def generate_schemas():
    """Generate JSON schemas from Pydantic models."""
    print("Generating JSON schemas from Pydantic models...")
    
    # Import models
    from app.common.models.request_models import CustomerRequest
    from app.common.models.response_models import CustomerResponse
    
    # Create the schemas directory if it doesn't exist
    schemas_dir = Path('api_spec/schemas')
    schemas_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate and save schemas
    models = [
        (CustomerRequest, 'customer_request.json'),
        (CustomerResponse, 'customer_response.json'),
    ]
    
    for model, filename in models:
        schema = model.model_json_schema()
        with open(schemas_dir / filename, 'w') as f:
            json.dump(schema, f, indent=2)
    
    print(f"JSON schemas saved to {schemas_dir}/")

if __name__ == '__main__':
    generate_openapi_spec()
    generate_schemas()