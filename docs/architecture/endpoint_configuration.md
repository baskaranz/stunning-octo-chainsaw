# Endpoint Configuration Guide

This document provides a comprehensive guide for configuring different types of endpoints in the Orchestrator API Service.

## Introduction

The Orchestrator API Service uses a configuration-driven approach to define API endpoints and their behavior. This means you can create new endpoints or modify existing ones simply by editing YAML configuration files, without changing any code.

Endpoints are defined in domain-specific configuration files located in the `config/domains/` directory. Each domain represents a logical group of related functionality (e.g., customers, orders, products).

## Endpoint Types

The service supports five main types of endpoints:

1. **Database Endpoints** - Expose data from database tables
2. **API Endpoints** - Expose data from external API services
3. **Feature Store Endpoints** - Expose data from Feast feature stores
4. **ML Service Endpoints** - Expose predictions from ML models
5. **Composite Endpoints** - Combine data from multiple sources

The `endpoint_type` property in the configuration explicitly identifies the endpoint type, which helps with validation and proper handling of the data flow.

## Configuration Structure

All endpoint configurations follow this general structure:

```yaml
endpoints:
  operation_name:
    description: "Description of what this endpoint does"
    endpoint_type: "database|api|feast|ml|composite"
    data_sources:
      - name: source_name
        type: database|api|feast|ml
        operation: operation_to_perform
        params:
          param1: value1
          param2: value2
    primary_source: source_name
    response_mapping: 
      field1: "$source_name.field1"
      field2: "$source_name.field2"
```

Key properties:
- `endpoint_type`: Defines the main type of endpoint
- `data_sources`: List of data sources to query
- `primary_source`: The main data source (used when response_mapping is null)
- `response_mapping`: How to map source data to the response structure

## Database Endpoints

Database endpoints retrieve data from SQL databases using predefined queries.

### Configuration

```yaml
endpoints:
  get_customer:
    description: "Get customer details from database"
    endpoint_type: "database"
    data_sources:
      - name: customer_data
        type: database
        source_id: default  # References a database connection in database.yaml
        operation: get_customer  # References a query in database.yaml
        params:
          customer_id: "$request.customer_id"  # Parameter from the request
    primary_source: customer_data
    response_mapping: null  # Use database results directly
```

### Database Operation Definition

Database operations are defined in `config/database.yaml`:

```yaml
database:
  operations:
    get_customer:
      query: "SELECT * FROM customers WHERE customer_id = :customer_id"
      params:
        - customer_id
```

## API Endpoints

API endpoints make requests to external API services and return their responses.

### Configuration

```yaml
endpoints:
  get_credit_score:
    description: "Get credit score from external API"
    endpoint_type: "api"
    data_sources:
      - name: credit_data
        type: api
        source_id: credit_api  # References an API source in api_sources.yaml
        operation: get_customer_credit
        params:
          customer_id: "$request.customer_id"
    primary_source: credit_data
    response_mapping: null  # Use API response directly
```

### API Source Definition

API sources are defined in `config/integrations/api_sources.yaml`:

```yaml
api:
  sources:
    credit_api:
      base_url: "http://api.example.com/credit"
      timeout: 5
      headers:
        Content-Type: "application/json"
        Authorization: "Bearer $ENV[API_TOKEN]"
      operations:
        get_customer_credit:
          method: GET
          path: "/scores/{customer_id}"
          path_params:
            - customer_id
```

## Feature Store Endpoints

Feature store endpoints retrieve data from a Feast feature store.

### Configuration

```yaml
endpoints:
  get_customer_features:
    description: "Get customer features from Feast"
    endpoint_type: "feast"
    data_sources:
      - name: customer_features
        type: feast
        source_id: default  # References a Feast source in feast_config.yaml
        operation: get_customer_features
        params:
          customer_id: "$request.customer_id"
          feature_refs:  # Optional - specific features to retrieve
            - "default/customer_features:customer_lifetime_value"
            - "default/customer_features:purchase_frequency"
    primary_source: customer_features
    response_mapping: null  # Use feature store results directly
```

### Feast Source Definition

Feast sources are defined in `config/integrations/feast_config.yaml`:

```yaml
feast:
  sources:
    default:
      repo_path: "./feature_repo"
      project: "default"
      default_customer_features:
        - "default/customer_features:customer_lifetime_value"
        - "default/customer_features:days_since_last_purchase"
        - "default/customer_features:purchase_frequency"
```

## ML Service Endpoints

ML service endpoints are fundamentally different from other endpoint types. While database, API, and feature store endpoints primarily fetch existing data, ML endpoints send input data to machine learning models for scoring/inference and receive predictions in return.

### Configuration

```yaml
endpoints:
  predict_churn_risk:
    description: "Get customer churn prediction"
    endpoint_type: "ml"
    data_sources:
      - name: churn_prediction
        type: ml
        source_id: churn_model  # References an ML model in ml_config.yaml
        operation: predict
        params:
          # Input features for the model to score (not query parameters)
          features:
            customer_id: "$request.customer_id"
            tenure: "$request.months_active"
            subscription_type: "$request.plan"
            monthly_charges: "$request.monthly_bill"
            # Can also use features from other data sources
            # recent_purchases: "$customer_data.purchase_count"
    primary_source: churn_prediction
    response_mapping:
      customer_id: "$request.customer_id"
      prediction_results:
        churn_probability: "$churn_prediction.probability"
        risk_level: "$churn_prediction.risk_category"
        confidence: "$churn_prediction.confidence_score"
```

### ML Service Definition

ML services are defined in `config/integrations/ml_config.yaml`:

```yaml
ml:
  sources:
    churn_model:
      base_url: "http://model-service.example.com/models"
      models:
        churn:
          endpoint: "/churn/predictions"
          method: "POST"  # Most ML scoring endpoints use POST
          timeout: 10
          headers:
            Content-Type: "application/json"
```

### Key Differences from Other Endpoint Types

1. **Input Data vs. Query Parameters**: ML endpoints send input data (features) to the model for scoring, rather than query parameters to retrieve existing data

2. **POST vs. GET**: ML scoring endpoints typically use POST requests to send feature data in the request body

3. **Inference vs. Retrieval**: The model performs inference (computation) on the input data to generate predictions, rather than simply retrieving stored data

4. **Feature Preparation**: Input features often need to be prepared or transformed before sending to the model, which may include:
   - Combining data from multiple sources
   - Normalizing or scaling values
   - Encoding categorical variables
   - Handling missing values

### Common ML Endpoint Patterns

#### Pattern 1: Direct Feature Input

The simplest pattern is where features are provided directly in the request:

```yaml
endpoints:
  predict_churn:
    description: "Predict customer churn from provided features"
    endpoint_type: "ml"
    data_sources:
      - name: churn_prediction
        type: ml
        source_id: churn_model
        operation: predict
        params:
          features:
            tenure: "$request.months_active"
            monthly_charges: "$request.monthly_charges"
            contract_type: "$request.contract_type"
    response_mapping:
      churn_probability: "$churn_prediction.probability"
```

#### Pattern 2: Database Features to ML

A common pattern is to fetch features from a database and send them to an ML service for scoring:

```yaml
endpoints:
  predict_churn_from_db:
    description: "Predict customer churn using features from database"
    endpoint_type: "composite"
    data_sources:
      # First, fetch customer features from database
      - name: customer_features
        type: database
        source_id: default
        operation: get_customer_features
        params:
          customer_id: "$request.customer_id"
      
      # Then send those features to ML model for scoring
      - name: churn_prediction
        type: ml
        source_id: churn_model
        operation: predict
        params:
          features:
            # Map database fields to the feature names expected by the model
            customer_id: "$request.customer_id"
            tenure: "$customer_features.tenure_months"
            monthly_charges: "$customer_features.monthly_bill"
            total_charges: "$customer_features.lifetime_value"
            contract_type: "$customer_features.contract_type"
    
    response_mapping:
      customer_id: "$request.customer_id"
      prediction:
        probability: "$churn_prediction.probability"
        risk_level: "$churn_prediction.risk_level"
```

#### Pattern 3: Feature Store to ML

Another common pattern uses a feature store (like Feast) to retrieve features for ML scoring:

```yaml
endpoints:
  predict_churn_from_feast:
    description: "Predict customer churn using features from Feast"
    endpoint_type: "composite"
    data_sources:
      - name: customer_features
        type: feast
        source_id: default
        operation: get_customer_features
        params:
          customer_id: "$request.customer_id"
      
      - name: churn_prediction
        type: ml
        source_id: churn_model
        operation: predict
        params:
          features: "$customer_features"  # Pass all features directly
    
    response_mapping:
      customer_id: "$request.customer_id" 
      churn_risk:
        probability: "$churn_prediction.probability"
        risk_level: "$churn_prediction.risk_level"
```

### Example of ML Endpoint in a Composite Flow

In a complete data flow, ML endpoints often receive features prepared from other data sources:

```yaml
endpoints:
  customer_risk_assessment:
    description: "Assess customer risk using multiple models"
    endpoint_type: "composite"
    data_sources:
      # First get customer data
      - name: customer_data
        type: database
        source_id: default
        operation: get_customer
        params:
          customer_id: "$request.customer_id"
      
      # Then get customer features
      - name: customer_features
        type: feast
        source_id: default
        operation: get_customer_features
        params:
          customer_id: "$request.customer_id"
      
      # Finally score the features using ML model
      - name: risk_prediction
        type: ml
        source_id: risk_model
        operation: predict
        params:
          features:
            # Combine data from multiple sources for scoring
            customer_id: "$request.customer_id"
            tenure_months: "$customer_data.tenure_months"
            lifetime_value: "$customer_features.customer_lifetime_value" 
            purchase_frequency: "$customer_features.purchase_frequency"
            recent_support_tickets: "$customer_data.ticket_count"
    
    response_mapping:
      customer_id: "$customer_data.customer_id"
      name: "$customer_data.name"
      risk_assessment:
        risk_score: "$risk_prediction.risk_score"
        risk_category: "$risk_prediction.risk_category"
        confidence: "$risk_prediction.confidence"
        contributing_factors: "$risk_prediction.feature_importance[*]"
```

## Composite Endpoints

Composite endpoints combine data from multiple sources (databases, APIs, feature stores, ML models) into a unified response.

### Configuration

```yaml
endpoints:
  get_customer_360:
    description: "Get comprehensive customer view"
    endpoint_type: "composite"
    data_sources:
      - name: profile
        type: database
        source_id: default
        operation: get_customer
        params:
          customer_id: "$request.customer_id"
      
      - name: features
        type: feast
        source_id: default
        operation: get_customer_features
        params:
          customer_id: "$request.customer_id"
      
      - name: credit_score
        type: api
        source_id: credit_api
        operation: get_customer_credit
        params:
          customer_id: "$request.customer_id"
      
      - name: churn_prediction
        type: ml
        source_id: churn_model
        operation: predict
        params:
          customer_id: "$request.customer_id"
          features: "$features"  # Use features from Feast
    
    response_mapping:
      customer_id: "$profile.customer_id"
      name: "$profile.name"
      email: "$profile.email"
      credit_info:
        score: "$credit_score.score"
        risk_tier: "$credit_score.risk_tier"
      behavior:
        lifetime_value: "$features.customer_lifetime_value"
        purchase_frequency: "$features.purchase_frequency"
      churn_risk:
        probability: "$churn_prediction.probability"
        risk_level: "$churn_prediction.risk_category"
```

### Orchestration Flow

The data orchestration flow for composite endpoints follows these steps:

1. Request Processor receives the API request
2. Data Orchestrator determines the execution plan
3. Data Source Adapters fetch data from each source
4. Data is combined according to the response mapping
5. Final response is returned to the client

### Response Mapping

The `response_mapping` section defines how data from different sources is combined into the final response.

Key features:
- Source references: `$source_name.field_name`
- Nested structures: Define objects and arrays in the response
- Array notation: `$source_name[*]` to include all items from an array
- Cross-source references: Use data from one source as input to another

## Best Practices

1. **Use explicit endpoint types** - Always specify the `endpoint_type` for clarity and validation
2. **Keep operations reusable** - Define operations in their respective config files so they can be used by multiple endpoints
3. **Use descriptive source names** - Choose meaningful names for data sources to make response mapping clearer
4. **Set reasonable timeouts** - Configure appropriate timeouts for API and external service sources
5. **Start simple** - Begin with simple endpoint types before creating complex composite endpoints
6. **Layer your data sources** - For complex orchestrations, consider building intermediate endpoints that can be used by other endpoints

## Complete Example

See the [Generic Orchestrator Example](../../example/README.md) for a complete working example of endpoint configuration.