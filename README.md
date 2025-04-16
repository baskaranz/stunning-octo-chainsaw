# Orkestra

A configurable API service that orchestrates data flows across multiple sources, including databases, external APIs, feature stores, and ML models.

## Overview

Orkestra serves as a middleware layer that:

1. Exposes a unified API for client applications
2. Orchestrates data flows across multiple backend systems
3. Combines and transforms data from various sources
4. Simplifies client integration with complex backend systems

You can use Orkestra in two ways:
- As a library in your Python projects (recommended)
- As a standalone service

## Features

- **Declarative Configuration**: Define APIs and data flows through YAML configuration
- **Multi-Source Orchestration**: Coordinate data retrieval and manipulation across:
  - Databases (for internal feature retrieval)
  - External APIs
  - Feature stores (Feast)
  - ML model services
- **Multiple Model Loading Strategies**:
  - HTTP API models (traditional approach)
  - Local artifact models (load models from filesystem)
  - Docker container models (run models in Docker)
  - ECR repository models (pull and run models from AWS ECR)
- **Dynamic Response Assembly**: Build responses by combining data from multiple sources
- **Flexible Transformation**: Transform data between sources and before returning responses
- **Execution Tracking**: Monitor and debug orchestration flows
- **Configuration Reloading**: Update configurations without service restart

## Architecture

The service is built around these core components:

- **API Layer**: Handles HTTP requests and routing
- **Orchestration Engine**: Coordinates data flows between sources
- **Data Source Adapters**: Connect to various backend systems
- **Configuration Engine**: Loads and manages configuration files

## Installation

### As a Library (Recommended)

Install from PyPI:

```bash
pip install orkestra
```

Or install from source:

```bash
git clone <repository-url>
cd orkestra
pip install -e .
```

### As a Standalone Service

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd orkestra
   ```

2. Create and activate a virtual environment:
   ```bash
   # Using venv (Python 3.8+)
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install all dependencies:
   ```bash
   # Option 1: Install all dependencies including development tools
   pip install -r requirements.txt
   
   # Option 2: Install minimal required dependencies
   pip install -e .
   
   # Option 3: Install with specific extras
   pip install -e ".[dev]"  # For development tools
   ```

## Quick Start

### Using as a Library

1. **Initialize a new project**:

   ```bash
   orkestra init my-orkestra-project
   cd my-orkestra-project
   ```

2. **Add your domain configurations**:

   Edit or create YAML files in the `config/domains/` directory.

3. **Run the service**:

   ```bash
   orkestra run --config-path ./config
   ```

4. **Access the API**:

   Open http://localhost:8000/docs in your browser to see the API documentation.

### Using as a Standalone Service

1. **Run the service**:

   ```bash
   python main.py
   ```

2. **Run the example**:

   ```bash
   # Run the iris example
   python example/run_iris_example.py
   ```

## Configuration

The service uses a configuration-driven approach with files located in the `config/` directory:

- `config.yaml`: Global application settings
- `database.yaml`: Database connection settings
- `domains/`: Domain-specific endpoint configurations (one file per domain)
- `integrations/`: External system configurations

### Endpoint Configuration Example

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

## Creating a Project with Only Configurations

The Orchestrator API Service is designed to be used as a library, where your project only needs to provide configurations without any code. This approach is ideal for data scientists and ML engineers who want to quickly expose models via an API.

### Library-only Project Structure

```
my-orchestrator-project/
├── config/
│   ├── config.yaml            # Global application settings
│   ├── database.yaml          # Database connection settings
│   ├── domains/
│   │   ├── model_a.yaml       # Domain configuration for Model A
│   │   ├── model_b.yaml       # Domain configuration for Model B
│   │   └── ...
│   └── integrations/
│       ├── api_sources.yaml   # External API configurations
│       ├── feast_config.yaml  # Feast feature store configuration
│       └── ml_config.yaml     # ML model configurations
├── requirements.txt           # Only needs orchestrator-api-service
└── README.md
```

### Minimal requirements.txt

```
orkestra>=0.1.0
```

### Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
orkestra run --config-path ./config
```

## Command Line Interface

The library provides a command-line interface (CLI) for working with Orkestra projects:

```bash
# Show help
orkestra --help

# Initialize a new project
orkestra init my-project

# Run the service
orkestra run --config-path ./config

# Run with auto-reload for development
orkestra run --reload --config-path ./config

# Show version
orkestra version
```

## Examples

For detailed examples of how to use the service, see the `example/` directory:

- **Basic Example**: Simple endpoints with direct responses
- **Iris Example**: Classification model with multiple data sources
- **Model Scoring**: Complex scoring models with various input sources

See the [Example README](example/README.md) for more details.

## API Documentation

API documentation is available at http://localhost:8000/docs when the service is running.

## Development

### Testing

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/path/to/test_file.py
```

### Linting and Type Checking

```bash
# Run linting
flake8 app/ tests/

# Run type checking
mypy app/ tests/
```

## License

[MIT License](LICENSE)