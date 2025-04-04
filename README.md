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

## Examples

For detailed examples of how to use the Orchestrator API Service, please see the [Examples README](examples/README.md).

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