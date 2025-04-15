# Generic Orchestrator API

This document describes the generic orchestrator API design and usage patterns for model scoring endpoints.

## Overview

The orchestrator API provides a consistent interface for model scoring that can be configured without code changes. It supports:

- Unified API structure with endpoints for different models
- Data retrieval from multiple sources (database, feature store, external APIs)
- Dynamic request handling with parameter mapping
- Consistent response formatting

## API Endpoints

### Base Endpoint

```
/orchestrator/model_scoring/{model_name}
```

Where `{model_name}` is the configuration-defined model identifier (e.g., `churn_pred`, `loan_pred`).

### HTTP Methods

- `GET /orchestrator/model_scoring/{model_name}/{entity_id}`: Score using entity lookup
- `POST /orchestrator/model_scoring/{model_name}`: Score using provided features
- `POST /orchestrator/model_scoring/{model_name}/{entity_id}`: Score using both entity lookup and provided features
- `GET /orchestrator/model_scoring`: List all available models

## Configuration Structure

Each model has its own dedicated configuration directory structure under `config/domains/`:

```
config/domains/model_scoring_{model_name}/
├── database.yaml                 # Domain-specific database operations
├── integrations/                 # Domain-specific integrations
│   ├── api_sources.yaml          # API connections for this model
│   ├── feast_config.yaml         # Feast settings for this model
│   └── ml_config.yaml            # ML model settings for this model
└── model_scoring_{model_name}.yaml   # Main domain endpoint configuration
```

The main domain configuration file follows the pattern:

```
model_scoring_{model_name}.yaml
```

### Configuration Format

```yaml
# Model Scoring Configuration
domain_id: model_scoring_{model_name}
description: "Description of the model API"

endpoints:
  predict:
    description: "Model prediction endpoint description"
    endpoint_type: "composite"
    
    # Schema definitions for documentation
    input_schema:
      type: "object"
      properties:
        # Entity ID and feature definitions
    
    output_schema:
      type: "object"
      properties:
        # Response format definition
    
    data_sources:
      # Database lookup data source
      - name: entity_data
        type: database
        operation: get_entity_data
        params:
          entity_id: "$request.path_params.entity_id"
        condition: "$request.path_params.entity_id != null"
      
      # Direct features data source
      - name: direct_features
        type: direct
        operation: use_request_features
        params: "$request.body"
        condition: "$request.body != null && Object.keys($request.body).length > 0"
      
      # ML model scoring step
      - name: prediction
        type: ml
        source_id: model_source
        operation: predict
        params:
          features:
            # Feature mapping with fallbacks
            feature1: "$entity_data.feature1 || $direct_features.feature1 || default_value"
            feature2: "$entity_data.feature2 || $direct_features.feature2 || default_value"
    
    # Response mapping to create a unified response
    response_mapping:
      entity_id: "$entity_data.id || $request.path_params.entity_id || 'unknown'"
      # Map other fields from data sources to response
```

## Example Usage

### Data Flow Patterns

The data flow through the orchestrator supports several patterns:

#### Database -> ML Pattern

This is the traditional pattern for model scoring:

1. **Request Parsing**: Extract path parameters, query parameters, and request body
2. **Database Retrieval**: Get data from database based on parameters
3. **Feature Assembly**: Transform database data into model-ready features
4. **Model Scoring**: Send features to ML model for scoring
5. **Response Assembly**: Format the results according to the response mapping

#### Feast -> ML Pattern (with Database Fallback)

This pattern uses a feature store for feature retrieval with automatic fallback to database:

1. **Request Parsing**: Extract entity ID from request
2. **Feature Retrieval**: Get features from Feast feature store
3. **Fallback Handling**: If Feast fails or is unavailable, automatically fall back to database
4. **Model Scoring**: Send features to ML model for scoring
5. **Response Assembly**: Format the results according to the response mapping

An example of this pattern can be found in the Iris example.

#### Composite Pattern

This pattern combines multiple data sources:

1. **Request Parsing**: Extract path parameters, query parameters, and request body
2. **Data Retrieval**: Get data from configured sources based on parameters
3. **Feature Assembly**: Combine and transform data into model-ready features
4. **Model Scoring**: Send features to ML model for scoring
5. **Response Assembly**: Format the results according to the response mapping

### Using with cURL

```bash
# Get prediction using entity ID
curl "http://localhost:8000/orchestrator/model_scoring/churn_pred/cust_1001"

# Get prediction with query parameters
curl "http://localhost:8000/orchestrator/model_scoring/loan_pred/applicant_123?loan_amount=25000&loan_term=36"

# Post features directly for scoring
curl -X POST "http://localhost:8000/orchestrator/model_scoring/churn_pred" \
  -H "Content-Type: application/json" \
  -d '{
    "company_size": "Medium", 
    "industry": "Technology",
    "contract_months": 12,
    "feature_usage_score": 0.67,
    "active_users": 42
  }'

# List available models
curl "http://localhost:8000/orchestrator/model_scoring"
```

### Using the Client Script

```bash
# Score with database lookup
python example/model_scoring_client.py credit-risk --id cust_1001

# Score with direct features
python example/model_scoring_client.py loan_pred --features "loan_amount=25000,loan_term=36,credit_score=720"

# Score with both lookup and additional parameters
python example/model_scoring_client.py product-recommender --id cust_1002 --context "current_page=electronics,recent_searches=laptop|headphones"
```

## Adding New Models

To add a new model to the orchestrator:

1. Create a domain configuration folder structure:
   ```
   mkdir -p config/domains/model_scoring_{model_name}/integrations
   ```

2. Create the main domain configuration file:
   ```
   config/domains/model_scoring_{model_name}.yaml
   ```

3. Create domain-specific database configuration:
   ```
   config/domains/model_scoring_{model_name}/database.yaml
   ```

4. Create domain-specific integration configurations:
   ```
   config/domains/model_scoring_{model_name}/integrations/ml_config.yaml
   ```

5. Define the data sources, feature mapping, and response structure in the main domain configuration
6. Add domain-specific database operations to retrieve entity data
7. Configure the ML model client in the domain's integration files

No code changes are required to the orchestrator API itself, as all logic is driven by configuration.

## Security Considerations

- Model names are validated against a safe pattern to prevent injection attacks
- Configuration is loaded from trusted sources only
- Input validation is performed before processing
- Error handling prevents leaking sensitive information