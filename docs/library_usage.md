# Using Orchestrator API Service as a Library

This guide explains how to use the Orchestrator API Service as a Python library in your projects.

## Installation

You can install the package from PyPI:

```bash
pip install orchestrator-api-service
```

Or install from source:

```bash
git clone <repository-url>
cd orchestrator-api-service
pip install -e .
```

## Creating a New Project

The easiest way to get started is to use the CLI to create a new project:

```bash
# Create a new project
orchestrator-api init my-orchestrator-project

# Navigate to the project directory
cd my-orchestrator-project
```

This will create a project with the following structure:

```
my-orchestrator-project/
├── config/
│   ├── config.yaml            # Global application settings
│   ├── database.yaml          # Database connection settings
│   ├── domains/
│   │   └── example.yaml       # Example domain configuration
│   └── integrations/
└── README.md
```

## Running the Service

Once you've created your project, you can run the service using the CLI:

```bash
# Run the service using the config files in the current directory
orchestrator-api run --config-path ./config

# For development with auto-reload
orchestrator-api run --reload --config-path ./config
```

By default, the service will start on http://localhost:8000.

## Configuration Files

The Orchestrator API Service uses YAML configuration files to define:

1. Global service settings
2. Database connections
3. Domain-specific endpoint configurations
4. Integration settings for external systems

### config.yaml

This file contains global settings for the service:

```yaml
# Global orchestrator configuration
app:
  name: "Orchestrator API Service"
  description: "API service for orchestrating data flows"
  version: "0.1.0"
  
server:
  host: "0.0.0.0"
  port: 8000
  
logging:
  level: "INFO"
```

### database.yaml

This file defines database connections:

```yaml
# Global database configuration
database:
  # Default database source
  sources:
    default:
      type: "sqlite"
      connection_string: "sqlite:///data/example.db"
      pool_size: 5
      max_overflow: 10
      pool_timeout: 30
```

### Domain Configuration

Domain configuration files are placed in the `config/domains/` directory and define API endpoints for a specific domain:

```yaml
# config/domains/model_scoring.yaml
domain_id: "model_scoring"
description: "Credit risk scoring model"

endpoints:
  predict:
    description: "Predict credit risk using customer data"
    endpoint_type: "composite"
    data_sources:
      - name: customer_data
        type: database
        operation: get_customer
        params:
          customer_id: "$request.path_params.entity_id"
      
      - name: risk_prediction
        type: ml
        source_id: credit_model
        operation: predict
        params:
          features:
            credit_score: "$customer_data.credit_score"
            income: "$customer_data.annual_income"
    
    response_mapping:
      customer_id: "$customer_data.customer_id"
      risk_score: "$risk_prediction.score"
      risk_tier: "$risk_prediction.risk_tier"
```

Each domain file will create routes with the pattern:
- `/orchestrator/{domain_id}/{endpoint_name}/{entity_id}`

For example, the above configuration would create the route:
- `/orchestrator/model_scoring/predict/{entity_id}`

### Integration Configuration

Integration configuration files are placed in the `config/integrations/` directory and define connections to external systems:

```yaml
# config/integrations/ml_config.yaml
ml:
  sources:
    credit_model:
      type: "http"
      base_url: "http://localhost:8501"
      endpoint: "/predict"
      timeout: 5000
```

## Accessing Your API

Once your service is running, you can:

1. View API documentation at http://localhost:8000/docs
2. Make requests to your configured endpoints

Example request:

```bash
# For a model_scoring domain with a predict endpoint
curl http://localhost:8000/orchestrator/model_scoring/predict/customer123
```

## Programmatic Usage

You can also use the library programmatically in your Python code:

```python
from orchestrator_api_service.app import create_app
import uvicorn
import os

# Set config path environment variable
os.environ["CONFIG_PATH"] = "./config"

# Create the app
app = create_app()

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Command Line Interface

The library provides a command line interface for common operations:

```bash
# Show help
orchestrator-api --help

# Initialize a new project
orchestrator-api init my-project

# Run the service
orchestrator-api run --config-path ./config

# Run with auto-reload for development
orchestrator-api run --reload --config-path ./config

# Show version
orchestrator-api version
```

## Examples

For more examples and detailed usage patterns, see the `example/` directory in the repository.

## Advanced Usage

For advanced usage including custom data sources, authentication, and deployment, please refer to the advanced documentation in the project repository.