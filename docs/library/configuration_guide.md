# Configuration Guide

This document explains the configuration options for Orchestrator API Service.

## Configuration Files

The service uses YAML configuration files to define its behavior. These files are typically organized in the following directory structure:

```
config/
├── config.yaml            # Global application settings
├── database.yaml          # Database connection settings
├── domains/
│   ├── domain1.yaml       # Domain-specific endpoint configurations
│   └── domain2.yaml
└── integrations/
    ├── api_sources.yaml   # External API configurations
    ├── feast_config.yaml  # Feature store configurations
    └── ml_config.yaml     # ML model configurations
```

## Global Configuration (config.yaml)

The `config.yaml` file contains global settings for the service:

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
  level: "INFO"  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL
  
execution:
  timeout: 60000  # Default timeout in milliseconds
  retries: 3
  
api:
  prefix: "/orchestrator"  # URL prefix for all API endpoints
  docs_url: "/docs"        # Path for Swagger UI
  redoc_url: "/redoc"      # Path for ReDoc UI
```

## Database Configuration (database.yaml)

The `database.yaml` file defines database connections:

```yaml
# Database configuration
database:
  # Database sources
  sources:
    default:
      type: "sqlite"  # Can be sqlite, postgresql, mysql, etc.
      connection_string: "sqlite:///data/example.db"
      pool_size: 5
      max_overflow: 10
      pool_timeout: 30
    
    # You can define multiple database sources
    reporting_db:
      type: "postgresql"
      connection_string: "postgresql://user:password@localhost:5432/reporting"
      pool_size: 10
  
  # Default settings for all operations
  defaults:
    timeout: 30000  # 30 seconds
    
  # Database operations
  operations:
    get_user_by_id:
      source_id: "default"  # Which database source to use
      query: "SELECT * FROM users WHERE id = :user_id"
      timeout: 5000  # Override default timeout for this operation
      
    get_product_details:
      source_id: "default"
      query: "SELECT * FROM products WHERE product_id = :product_id"
```

## Domain Configuration

Domain configurations are stored in the `domains/` directory. Each file defines endpoints for a specific domain:

```yaml
# domains/user_management.yaml
domain_id: "user_management"
description: "User management endpoints"

# Define endpoints for this domain
endpoints:
  get_user:
    description: "Get user by ID"
    endpoint_type: "composite"
    method: "get"
    
    data_sources:
      - name: user_data
        type: database
        operation: get_user_by_id
        params:
          user_id: "$request.path_params.user_id"
      
      - name: user_preferences
        type: database
        operation: get_user_preferences
        params:
          user_id: "$request.path_params.user_id"
    
    response_mapping:
      user_id: "$user_data.id"
      username: "$user_data.username"
      email: "$user_data.email"
      preferences: "$user_preferences"
```

## Endpoint Types

The service supports several endpoint types:

### Direct Endpoint

Direct endpoints return a static response with variable substitution:

```yaml
endpoints:
  hello:
    description: "Simple hello endpoint"
    endpoint_type: "direct"
    method: "get"
    response_type: "json"
    
    response:
      message: "Hello, $request.path_params.name!"
      timestamp: "$system.timestamp"
```

### Composite Endpoint

Composite endpoints retrieve data from multiple sources and assemble a response:

```yaml
endpoints:
  predict:
    description: "Predict user behavior"
    endpoint_type: "composite"
    
    data_sources:
      - name: user_data
        type: database
        operation: get_user
        params:
          user_id: "$request.path_params.user_id"
      
      - name: prediction
        type: ml
        source_id: behavior_model
        operation: predict
        params:
          features:
            age: "$user_data.age"
            tenure: "$user_data.tenure"
    
    response_mapping:
      user_id: "$user_data.id"
      prediction: "$prediction.result"
      confidence: "$prediction.confidence"
```

## Integration Configurations

### API Sources (api_sources.yaml)

Define external API integrations:

```yaml
api:
  sources:
    weather_api:
      base_url: "https://api.example.com"
      timeout: 5000
      retry_count: 3
      
      operations:
        get_current_weather:
          path: "/weather/current"
          method: "get"
          headers:
            Content-Type: "application/json"
          params:
            city: "{city}"
            units: "metric"
```

### Feast Feature Store (feast_config.yaml)

Configure Feast feature store integration:

```yaml
feast:
  sources:
    default:
      repo_path: "./feature_repo"
      feature_server_type: "local"  # local, remote, or hybrid
      
      feature_services:
        user_features:
          features:
            - "user:age"
            - "user:tenure"
            - "user:activity_level"
```

### ML Models (ml_config.yaml)

Configure ML model integration:

```yaml
ml:
  sources:
    default:
      type: "http"
      base_url: "http://localhost:8501"
      timeout: 5000
      
    behavior_model:
      type: "local"
      model_path: "./models/behavior_model.pkl"
      model_type: "sklearn"
```

## Using Template Expressions

The configuration supports template expressions for dynamic values:

- `$request.path_params.name` - Access path parameters
- `$request.query_params.filter` - Access query parameters
- `$request.body.data` - Access request body
- `$system.timestamp` - Current timestamp
- `$data_source_name.field` - Access data from a data source

## Best Practices

1. **Organize by domain**: Create separate domain files for different areas of functionality
2. **Use descriptive names**: Choose clear names for domains, endpoints, and data sources
3. **Reuse operations**: Define database operations once and reuse them across endpoints
4. **Layer your configurations**: Use domain-specific integration files for specialized settings
5. **Document your endpoints**: Always include descriptions for domains and endpoints

For more examples and detailed usage patterns, see the [example projects](../../examples/).