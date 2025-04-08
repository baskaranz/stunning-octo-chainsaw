# Orchestrator API Service: Onboarding Guide

This guide provides step-by-step instructions for onboarding new use cases, domains, and endpoints to the Orchestrator API Service.

## Table of Contents

1. [Understanding the Orchestrator](#understanding-the-orchestrator)
2. [Typical Data Flow Patterns](#typical-data-flow-patterns)
3. [Step-by-Step Onboarding](#step-by-step-onboarding)
4. [Sample Configurations](#sample-configurations)
5. [Testing Your Endpoint](#testing-your-endpoint)
6. [Troubleshooting](#troubleshooting)

## Understanding the Orchestrator

The Orchestrator API Service is designed as a configuration-driven middleware that:

- Retrieves data from multiple sources (databases, APIs, feature stores)
- Transforms and combines this data
- Sends it to ML models for scoring/inference
- Formats and returns the results

All of this is done through YAML configuration, with minimal or no code changes required.

## Typical Data Flow Patterns

The orchestrator supports several common patterns:

| Pattern | Description | Use Case |
|---------|-------------|----------|
| Database → ML | Retrieves features from database tables and sends to ML model | Credit risk scoring |
| API → ML | Retrieves data from external APIs and sends to ML model | Churn prediction |
| Feast → ML | Retrieves features from Feast feature store and sends to ML model | Product recommendations |
| Multi-source → ML | Combines data from multiple sources and sends to ML model | Loan approval |

## Step-by-Step Onboarding

### 1. Identify Your Domain

A domain represents a logical grouping of related functionality (e.g., credit-risk, fraud-detection, product-recommendation).

For each domain:
- Determine the model(s) needed
- Identify data sources required
- Define the response format

### 2. Set Up Directory Structure

Create a configuration directory for your domain:

```
my_orchestrator_app/
├── config/
│   ├── config.yaml               # Global settings
│   ├── database.yaml             # Database connections and queries
│   ├── domains/
│   │   └── my_domain.yaml        # Domain endpoint configuration
│   └── integrations/
│       ├── api_sources.yaml      # API connections
│       ├── feast_config.yaml     # Feast settings
│       └── ml_config.yaml        # ML model settings
```

### 3. Configure Data Sources

#### 3.1 For Database Sources

Add your database operations to `database.yaml`:

```yaml
database:
  operations:
    get_my_entity:
      query: "SELECT * FROM my_table WHERE id = :entity_id"
      params:
        - entity_id
```

#### 3.2 For API Sources

Add your API endpoints to `api_sources.yaml`:

```yaml
api:
  sources:
    my_api:
      base_url: "https://api.example.com"
      timeout: 5
      headers:
        Authorization: "Bearer $ENV[MY_API_TOKEN]"
      operations:
        get_entity_data:
          method: GET
          path: "/entities/{entity_id}"
          path_params:
            - entity_id
```

#### 3.3 For Feast Sources

Add your feature services to `feast_config.yaml`:

```yaml
feast:
  sources:
    my_feature_store:
      repo_path: "./my_feature_repo"
      project: "default"
      feature_services:
        my_features:
          features:
            - "entity:feature1"
            - "entity:feature2"
```

#### 3.4 For ML Models

Add your model configuration to `ml_config.yaml`:

```yaml
ml:
  sources:
    my_model:
      base_url: "http://my-model-service:5000"
      timeout: 10
      headers:
        Content-Type: "application/json"
      models:
        default:
          endpoint: "/predict"
          method: "POST"
```

### 4. Configure Domain Endpoint

Create a domain configuration file (e.g., `domains/my_domain.yaml`):

```yaml
domain_id: my_domain
description: "My domain description"

endpoints:
  predict:
    description: "Make prediction using my model"
    endpoint_type: "composite"
    
    data_sources:
      # Source 1: Get data from database
      - name: entity_data
        type: database
        source_id: default
        operation: get_my_entity
        params:
          entity_id: "$request.path_params.entity_id"
      
      # Source 2: Get data from API
      - name: external_data
        type: api
        source_id: my_api
        operation: get_entity_data
        params:
          entity_id: "$request.path_params.entity_id"
      
      # Source 3: Get features from Feast
      - name: features
        type: feast
        source_id: my_feature_store
        operation: get_features
        params:
          entity_id: "$request.path_params.entity_id"
      
      # Source 4: Call ML model
      - name: prediction
        type: ml
        source_id: my_model
        operation: predict
        params:
          features:
            feature1: "$entity_data.feature1"
            feature2: "$external_data.feature2"
            feature3: "$features.feature3"
    
    # Define response format
    response_mapping:
      entity_id: "$request.path_params.entity_id"
      prediction:
        score: "$prediction.score"
        confidence: "$prediction.confidence"
      factors: "$prediction.factors"
```

### 5. Start the Orchestrator Service

Launch the service with your configuration:

```bash
python main.py --config /path/to/your/config/config.yaml
```

Your endpoint will be available at:
```
/orchestrator/my_domain/predict/{entity_id}
```

## Sample Configurations

Below are configurations for common data flow patterns:

### Database → ML

```yaml
# Domain configuration
endpoints:
  predict:
    data_sources:
      - name: db_data
        type: database
        source_id: default
        operation: get_entity_data
        params:
          entity_id: "$request.path_params.entity_id"
      
      - name: prediction
        type: ml
        source_id: my_model
        operation: predict
        params:
          features:
            feature1: "$db_data.feature1"
            feature2: "$db_data.feature2"
```

### API → ML

```yaml
# Domain configuration
endpoints:
  predict:
    data_sources:
      - name: api_data
        type: api
        source_id: external_api
        operation: get_entity
        params:
          entity_id: "$request.path_params.entity_id"
      
      - name: prediction
        type: ml
        source_id: my_model
        operation: predict
        params:
          features:
            feature1: "$api_data.feature1"
            feature2: "$api_data.feature2"
```

### Feast → ML

```yaml
# Domain configuration
endpoints:
  predict:
    data_sources:
      - name: features
        type: feast
        source_id: my_feature_store
        operation: get_features
        params:
          entity_id: "$request.path_params.entity_id"
          feature_refs:
            - "entity:feature1"
            - "entity:feature2"
      
      - name: prediction
        type: ml
        source_id: my_model
        operation: predict
        params:
          features: "$features"  # Pass all features directly
```

### Mixed Sources → ML

```yaml
# Domain configuration
endpoints:
  predict:
    data_sources:
      - name: db_data
        type: database
        source_id: default
        operation: get_entity_data
        params:
          entity_id: "$request.path_params.entity_id"
      
      - name: api_data
        type: api
        source_id: external_api
        operation: get_additional_data
        params:
          entity_id: "$request.path_params.entity_id"
      
      - name: features
        type: feast
        source_id: my_feature_store
        operation: get_features
        params:
          entity_id: "$request.path_params.entity_id"
      
      - name: prediction
        type: ml
        source_id: my_model
        operation: predict
        params:
          features:
            db_feature: "$db_data.feature"
            api_feature: "$api_data.feature"
            feast_feature: "$features.feature"
```

## Testing Your Endpoint

### Using curl

```bash
# GET request
curl "http://localhost:8000/orchestrator/my_domain/predict/entity_123"

# POST request with body
curl -X POST "http://localhost:8000/orchestrator/my_domain/predict/entity_123" \
  -H "Content-Type: application/json" \
  -d '{"context": {"parameter1": "value1", "parameter2": "value2"}}'
```

### Using the provided client

```bash
python example/api_client.py my-domain --id entity_123
```

## Troubleshooting

### Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| 404 Not Found | Domain/endpoint not found | Check domain_id and endpoint name in YAML file |
| 500 Internal Server Error | Error in configuration or data source | Check logs for detailed error message |
| Empty/null values in response | Missing data or reference error | Check data source response and parameter references |
| Missing or incorrect features | Incorrect data mapping | Verify feature mapping in data_sources section |

### Debug Mode

Enable debug logging in `config.yaml`:

```yaml
logging:
  level: "DEBUG"
```

### Checking Endpoint Configuration

To verify your endpoint configuration is loaded correctly:

```bash
curl "http://localhost:8000/orchestrator/domains"
```

This will list all available domains and endpoints.

### Checking Data Source Output

You can add a special debug endpoint to your domain to check raw data source output:

```yaml
endpoints:
  debug:
    description: "Debug data sources"
    endpoint_type: "composite"
    data_sources:
      # Add the data source you want to debug
      - name: debug_data
        type: database
        source_id: default
        operation: get_my_entity
        params:
          entity_id: "$request.path_params.entity_id"
    
    # Return the raw data
    response_mapping: "$debug_data"
```

Then call:
```bash
curl "http://localhost:8000/orchestrator/my_domain/debug/entity_123"
```