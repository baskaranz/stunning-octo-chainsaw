# Orchestrator API Service

A configurable API service that orchestrates data flows across multiple sources, including databases, external APIs, feature stores, and ML models.

## Overview

The Orchestrator API Service serves as a middleware layer that:

1. Exposes a unified API for client applications
2. Orchestrates data flows across multiple backend systems
3. Combines and transforms data from various sources
4. Simplifies client integration with complex backend systems

## Features

- **Declarative Configuration**: Define APIs and data flows through YAML configuration
- **Multi-Source Orchestration**: Coordinate data retrieval and manipulation across:
  - Databases
  - External APIs
  - Feature stores (Feast)
  - ML model services
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

## Getting Started

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies:

```bash
pip install -e .
```

### Running the Service

```bash
python main.py
```

The service will start on http://localhost:8000 by default.

## Configuration

Configuration files are located in the `config/` directory:

- `config.yaml`: Global application settings
- `database.yaml`: Database connection settings
- `domains/`: Domain-specific endpoint configurations
- `integrations/`: External system configurations

### Endpoint Configuration

The Orchestrator API Service supports configuring different types of endpoints through YAML configuration files. You can define endpoints that:

1. **Expose Database Data**: Query database tables and return results
   ```yaml
   endpoints:
     get_customer:
       description: "Get customer details from database"
       endpoint_type: "database"
       data_sources:
         - name: customer_data
           type: database
           operation: get_customer
           params:
             customer_id: "$request.customer_id"
       primary_source: customer_data
       response_mapping: null  # Use database results directly
   ```

2. **Expose External API Data**: Call external APIs and return their responses
   ```yaml
   endpoints:
     get_credit_score:
       description: "Get credit score from external API"
       endpoint_type: "api"
       data_sources:
         - name: credit_data
           type: api
           operation: get_customer_credit
           params:
             customer_id: "$request.customer_id"
       primary_source: credit_data
       response_mapping: null  # Use API response directly
   ```

3. **Expose Feature Store Data**: Fetch and return data from Feast feature store
   ```yaml
   endpoints:
     get_customer_features:
       description: "Get customer features from Feast"
       endpoint_type: "feast"
       data_sources:
         - name: customer_features
           type: feast
           operation: get_customer_features
           params:
             customer_id: "$request.customer_id"
       primary_source: customer_features
       response_mapping: null  # Use feature store results directly
   ```

4. **Combine Multiple Data Sources**: Orchestrate data from multiple sources
   ```yaml
   endpoints:
     get_customer_360:
       description: "Get comprehensive customer view"
       endpoint_type: "composite"
       data_sources:
         - name: profile
           type: database
           operation: get_customer
           params:
             customer_id: "$request.customer_id"
         - name: features
           type: feast
           operation: get_customer_features
           params:
             customer_id: "$request.customer_id"
       response_mapping:
         id: "$profile.customer_id"
         name: "$profile.name"
         email: "$profile.email"
         lifetime_value: "$features.customer_lifetime_value"
         purchase_frequency: "$features.purchase_frequency"
   ```

For more detailed configuration examples, see the [Example README](example/README.md).

## Examples

The repository includes a generic orchestrator example that demonstrates:

1. **Model Scoring**: Shows integration between databases and ML services for different model types:
   - Credit risk scoring model
   - Product recommendation model

2. **Multi-Source Data Flow**: Demonstrates retrieving and combining data from:
   - Database tables
   - Request parameters
   - External APIs

For more details, see the [Example README](example/README.md).

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