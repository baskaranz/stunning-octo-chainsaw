# Project Structure Guide

This guide explains the recommended project structure when using Orchestrator API Service as a library.

## Basic Project Structure

When you create a new project using `orchestrator-api init`, it creates the following structure:

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

This is the minimal configuration required to run the service. For more complex projects, you may want to expand on this structure.

## Recommended Project Structure

For a production-ready project, we recommend the following structure:

```
my-orchestrator-project/
├── config/
│   ├── config.yaml                      # Global settings
│   ├── database.yaml                    # Database settings
│   ├── domains/
│   │   ├── domain1.yaml                 # Domain configurations
│   │   ├── domain2.yaml
│   │   └── domain3/                     # Complex domain with subdirectory
│   │       ├── domain3.yaml             # Main domain config
│   │       ├── database.yaml            # Domain-specific database config
│   │       └── integrations/            # Domain-specific integrations
│   │           ├── api_sources.yaml
│   │           └── ml_config.yaml
│   └── integrations/                    # Global integrations
│       ├── api_sources.yaml             # External API configurations
│       ├── feast_config.yaml            # Feature store configurations
│       └── ml_config.yaml               # ML model configurations
├── data/                                # Data directory
│   └── local.db                         # Local SQLite database
├── logs/                                # Log files
├── scripts/                             # Utility scripts
│   ├── backup_config.py
│   └── reload_config.py
├── tests/                               # Test configurations
│   └── postman/                         # Postman collections for testing
├── .env                                 # Environment variables
├── .gitignore                           # Git ignore file
├── README.md                            # Project documentation
├── requirements.txt                     # Project dependencies
└── run.py                               # Custom runner script (optional)
```

## Configuration Organization

### Global vs. Domain-Specific Configuration

- **Global Configuration**: Settings that apply to all domains are placed in the root `config/` directory.
- **Domain-Specific Configuration**: Settings that apply only to a specific domain are placed in a subdirectory under `domains/`.

For example:

```
config/
├── database.yaml                  # Global database config
└── domains/
    └── user_management/
        ├── user_management.yaml   # Main domain config
        ├── database.yaml          # Domain-specific database config
        └── integrations/
            └── api_sources.yaml   # Domain-specific API config
```

### Configuration Files

Here's a breakdown of the recommended configuration files:

1. **config.yaml**: Global service settings
   - App name, description, version
   - Server settings (host, port)
   - Logging configuration
   - API settings

2. **database.yaml**: Database connections and operations
   - Database sources
   - Connection parameters
   - Operations (queries)

3. **domains/[domain].yaml**: Domain endpoints
   - Domain ID and description
   - Endpoint definitions
   - Data source mappings
   - Response mappings

4. **integrations/api_sources.yaml**: External API configurations
   - API endpoints
   - Authentication settings
   - Timeout and retry settings

5. **integrations/feast_config.yaml**: Feature store settings
   - Repository path
   - Feature services
   - Connection settings

6. **integrations/ml_config.yaml**: ML model configurations
   - Model paths
   - Serving endpoints
   - Model parameters

## Custom Runner Script

For more control over the service startup, you can create a custom runner script:

```python
#!/usr/bin/env python3
# run.py

import os
import sys
from orchestrator_api_service.cli import run_server

def main():
    # Set environment variables
    os.environ["CONFIG_PATH"] = os.path.join(os.path.dirname(__file__), "config")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run the Orchestrator API Service')
    parser.add_argument('--port', type=int, default=8000, help='Port to run on')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    args = parser.parse_args()
    
    # Run the server
    run_server(
        host="0.0.0.0",
        port=args.port,
        reload=args.reload,
        config_path=os.environ["CONFIG_PATH"]
    )

if __name__ == "__main__":
    main()
```

## Environment Variables

Using environment variables is recommended for configuration that varies between environments:

```
# .env
ORCHESTRATOR_CONFIG_PATH=/path/to/config
DB_PASSWORD=secure_password
ML_MODEL_PATH=/path/to/models
```

Then load these in your custom run script:

```python
# Load environment variables
from dotenv import load_dotenv
load_dotenv()
```

## Git Integration

For version control with Git, use a `.gitignore` file to exclude sensitive data and temporary files:

```
# .gitignore
*.db
*.log
__pycache__/
.env
.venv/
logs/
data/local*
```

## Multi-Environment Setup

For projects deployed across multiple environments, consider this structure:

```
config/
├── base/                      # Base configurations
│   ├── config.yaml
│   └── domains/
├── development/               # Development-specific overrides
│   ├── config.yaml
│   └── database.yaml
├── staging/                   # Staging-specific overrides
│   ├── config.yaml
│   └── database.yaml
└── production/                # Production-specific overrides
    ├── config.yaml
    └── database.yaml
```

Then specify the environment in your run script:

```python
# Set environment
env = os.environ.get("ENVIRONMENT", "development")
os.environ["CONFIG_PATH"] = os.path.join(os.path.dirname(__file__), f"config/{env}")
```

## Best Practices

1. **Keep domains separate**: Each domain should have its own configuration file
2. **Use domain-specific subdirectories** for complex domains
3. **Version control your configurations**, excluding sensitive data
4. **Use environment variables** for sensitive or environment-specific settings
5. **Implement a logging strategy** with appropriate log rotation
6. **Document your project structure** in the README.md file
7. **Include example configurations** for new developers