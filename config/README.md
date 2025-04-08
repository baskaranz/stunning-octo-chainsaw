# Configuration Architecture

This document explains how the various configuration files in the Orchestrator API Service work together to define endpoints, data flows, and integrations with a focus on model scoring.

## Configuration Overview

The Orchestrator API Service uses a hierarchical configuration structure to define:
- Global application settings
- Database connections and operations
- External API endpoints
- Feature store configurations
- ML model integrations
- Domain-specific model scoring endpoints

The core philosophy is **configuration-driven development**: adding new model scoring endpoints should require minimal or no code changes, just configuration.

## Configuration File Structure

```
config/
├── config.yaml                 # Global application settings
├── database.yaml               # Database connections and queries
├── domains/                    # Endpoint definitions by domain
│   ├── model_scoring_credit_risk.yaml
│   ├── model_scoring_churn_pred.yaml
│   ├── model_scoring_loan_pred.yaml
│   └── model_scoring_product_recommender.yaml
└── integrations/               # External system configurations
    ├── api_sources.yaml        # External API definitions
    ├── feast_config.yaml       # Feature store connections
    ├── ml_generic_example.yaml # ML model service definitions
    └── mock_services.yaml      # Mock service configurations
```

## Configuration Hierarchy and Relationships

```
┌───────────────────────────────────────────────────────────────────────────┐
│                              config.yaml                                   │
│                                                                           │
│   Global settings: logging, server, cache, etc.                           │
└───────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────┬─────────────┴─────────────┬─────────────────────┐
│    database.yaml        │    domains/*.yaml         │  integrations/*.yaml│
│                         │                           │                     │
│ ┌─────────────────────┐ │ ┌─────────────────────┐  │ ┌─────────────────┐ │
│ │Database Connections │ │ │Model Scoring Config │  │ │External Systems │ │
│ │  - source_id        │◄┼─┤  - data_sources     │──┼►│  - source_id    │ │
│ │  - connection_string│ │ │  - endpoint_type    │  │ │  - base_url     │ │
│ └─────────────────────┘ │ └─────────────────────┘  │ └─────────────────┘ │
│                         │                           │                     │
│ ┌─────────────────────┐ │ ┌─────────────────────┐  │ ┌─────────────────┐ │
│ │Database Operations  │ │ │Feature Definitions  │  │ │API Operations   │ │
│ │  - operation name   │◄┼─┤  - feature mapping  │  │ │  - methods      │ │
│ │  - SQL query        │ │ │  - transformations  │  │ │  - endpoints    │ │
│ └─────────────────────┘ │ └─────────────────────┘  │ └─────────────────┘ │
│                         │                           │                     │
│                         │ ┌─────────────────────┐  │ ┌─────────────────┐ │
│                         │ │Response Mapping     │  │ │ML Models        │ │
│                         │ │  - field mapping    │  │ │  - models       │ │
│                         │ │  - transformations  │  │ │  - endpoints    │ │
│                         │ └─────────────────────┘  │ └─────────────────┘ │
│                         │                           │                     │
│                         │                           │ ┌─────────────────┐ │
│                         │                           │ │Feast Features   │ │
│                         │                           │ │  - repo_path    │ │
│                         │                           │ │  - feature_refs │ │
│                         │                           │ └─────────────────┘ │
└─────────────────────────┴───────────────────────┬──┴─────────────────────┘
                                                  │
                                                  ▼
     ┌──────────────────────────────────────────────────────────────────┐
     │                  Model Scoring API Endpoints                      │
     │                                                                   │
     │  - /orchestrator/model_scoring/credit_risk/{customer_id}         │
     │  - /orchestrator/model_scoring/churn_pred/{customer_id}          │
     │  - /orchestrator/model_scoring/product_recommender/{customer_id} │
     └──────────────────────────────────────────────────────────────────┘
```

# Model Scoring Examples

The Orchestrator API supports three primary data source patterns for model scoring:

| Data Source | Model Use Case | Example Endpoint |
|-------------|---------------|------------------|
| **Database** | Credit Risk Scoring | `/orchestrator/model_scoring/credit_risk/{customer_id}` |
| **External API** | Customer Churn Prediction | `/orchestrator/model_scoring/churn_pred/{customer_id}` |
| **Feast Feature Store** | Product Recommendations | `/orchestrator/model_scoring/product_recommender/{customer_id}` |

Each pattern demonstrates how to:
1. Configure data sources in YAML
2. Map source data to ML model features 
3. Format response data for the client

## Example 1: Credit Risk Model with Database Data

This example demonstrates retrieving customer data from a database to score credit risk.

**Key Features:**
- Fetches customer profile and credit history from database
- Maps database fields to ML model features
- Returns comprehensive risk assessment with explanation

### API Endpoint

```
GET /orchestrator/model_scoring/credit_risk/cust_1001
```

### Sample Response

```json
{
  "customer_id": "cust_1001",
  "name": "John Smith",
  "risk_score": {
    "score": 82,
    "risk_tier": "Low",
    "default_probability": 0.12,
    "confidence": 0.95
  },
  "credit_profile": {
    "credit_score": 720,
    "debt_to_income": 0.28,
    "payment_history_score": 0.92
  },
  "key_factors": [
    {"factor": "excellent_payment_history", "impact": 0.45},
    {"factor": "low_debt_ratio", "impact": 0.30},
    {"factor": "stable_income", "impact": 0.25}
  ],
  "recommended_actions": [
    {"action": "eligible_for_rate_decrease", "confidence": 0.92},
    {"action": "pre_approved_credit_increase", "confidence": 0.88}
  ]
}
```

### Configuration Files

<details>
<summary><b>Domain Configuration (domains/model_scoring_credit_risk.yaml)</b></summary>

```yaml
domain_id: model_scoring_credit_risk
description: "Credit risk assessment model API"

endpoints:
  predict:
    description: "Predict credit risk using customer data from database"
    endpoint_type: "composite"
    
    data_sources:
      # Get customer data from database
      - name: customer_data
        type: database
        source_id: default
        operation: get_customer
        params:
          customer_id: "$request.path_params.customer_id"
      
      # Get credit history from database
      - name: credit_history
        type: database
        source_id: default
        operation: get_credit_history
        params:
          customer_id: "$request.path_params.customer_id"
      
      # Call ML model for scoring
      - name: risk_prediction
        type: ml
        source_id: credit_model
        operation: predict
        params:
          features:
            customer_id: "$customer_data.customer_id"
            age: "$customer_data.age"
            income: "$customer_data.annual_income"
            debt_ratio: "$customer_data.debt_to_income"
            credit_score: "$credit_history.credit_score"
            payment_history: "$credit_history.payment_history_score"
    
    # Format the final response
    response_mapping:
      customer_id: "$customer_data.customer_id"
      name: "$customer_data.name"
      risk_score:
        score: "$risk_prediction.score"
        risk_tier: "$risk_prediction.risk_tier"
        default_probability: "$risk_prediction.default_probability"
        confidence: "$risk_prediction.confidence"
      credit_profile:
        credit_score: "$credit_history.credit_score"
        debt_to_income: "$customer_data.debt_to_income"
        payment_history_score: "$credit_history.payment_history_score"
      key_factors: "$risk_prediction.key_factors"
      recommended_actions: "$risk_prediction.recommended_actions"
```
</details>

<details>
<summary><b>Database Configuration (database.yaml)</b></summary>

```yaml
database:
  sources:
    default:
      connection_string: "sqlite:///customer360.db"
      # Connection settings...
  
  operations:
    get_customer:
      query: "SELECT * FROM customers WHERE customer_id = :customer_id"
      params:
        - customer_id
    
    get_credit_history:
      query: "SELECT * FROM credit_history WHERE customer_id = :customer_id"
      params:
        - customer_id
```
</details>

<details>
<summary><b>ML Model Configuration (integrations/ml_generic_example.yaml)</b></summary>

```yaml
ml:
  sources:
    credit_model:
      base_url: "http://localhost:5002/models"
      timeout: 5
      headers:
        Content-Type: "application/json"
      models:
        credit_risk:
          endpoint: "/credit-risk/predict"
          method: "POST"
```
</details>

## Example 2: Churn Prediction with External API Data

This example demonstrates retrieving customer data from external APIs to predict customer churn risk.

**Key Features:**
- Fetches customer profile from one API
- Fetches usage data from another API
- Combines data from multiple sources for ML model
- Returns churn prediction with contributing factors

### API Endpoint

```
GET /orchestrator/model_scoring/churn_pred/cust_2002
```

### Sample Response

```json
{
  "customer_id": "cust_2002",
  "name": "Jane Williams",
  "churn_prediction": {
    "probability": 0.27,
    "risk_level": "Medium",
    "confidence": 0.89
  },
  "customer_profile": {
    "subscription": "Premium",
    "tenure": 18,
    "monthly_charges": 89.99
  },
  "key_factors": [
    {"factor": "recent_support_calls", "impact": 0.35},
    {"factor": "reduced_usage", "impact": 0.25},
    {"factor": "price_sensitivity", "impact": 0.20}
  ],
  "retention_actions": [
    {"action": "offer_loyalty_discount", "confidence": 0.87},
    {"action": "proactive_support_outreach", "confidence": 0.78},
    {"action": "suggest_different_plan", "confidence": 0.65}
  ]
}
```

### Configuration Files

<details>
<summary><b>Domain Configuration (domains/model_scoring_churn_pred.yaml)</b></summary>

```yaml
domain_id: model_scoring_churn_pred
description: "Customer churn prediction model API"

endpoints:
  predict:
    description: "Predict customer churn using data from external API"
    endpoint_type: "composite"
    
    data_sources:
      # Get customer profile from external API
      - name: customer_profile
        type: api
        source_id: customer_api
        operation: get_customer_profile
        params:
          customer_id: "$request.path_params.customer_id"
      
      # Get usage data from external API
      - name: usage_data
        type: api
        source_id: usage_api
        operation: get_customer_usage
        params:
          customer_id: "$request.path_params.customer_id"
          months: 6
      
      # Call ML model for churn prediction
      - name: churn_prediction
        type: ml
        source_id: churn_model
        operation: predict
        params:
          features:
            customer_id: "$customer_profile.id"
            subscription_type: "$customer_profile.subscription_plan"
            tenure_months: "$customer_profile.tenure"
            monthly_charges: "$customer_profile.monthly_charges"
            total_charges: "$customer_profile.total_charges"
            usage_level: "$usage_data.average_usage"
            support_calls: "$usage_data.support_interactions"
            recent_outages: "$usage_data.service_outages"
    
    # Format the final response
    response_mapping:
      customer_id: "$customer_profile.id"
      name: "$customer_profile.name"
      churn_prediction:
        probability: "$churn_prediction.churn_probability"
        risk_level: "$churn_prediction.risk_level"
        confidence: "$churn_prediction.confidence"
      customer_profile:
        subscription: "$customer_profile.subscription_plan"
        tenure: "$customer_profile.tenure"
        monthly_charges: "$customer_profile.monthly_charges"
      key_factors: "$churn_prediction.contributing_factors"
      retention_actions: "$churn_prediction.recommended_actions"
```
</details>

<details>
<summary><b>API Configuration (integrations/api_sources.yaml)</b></summary>

```yaml
api:
  sources:
    customer_api:
      base_url: "http://api.example.com/customers"
      timeout: 5
      headers:
        Content-Type: "application/json"
        Authorization: "Bearer $ENV[CUSTOMER_API_TOKEN]"
      operations:
        get_customer_profile:
          method: GET
          path: "/{customer_id}"
          path_params:
            - customer_id
    
    usage_api:
      base_url: "http://api.example.com/usage"
      timeout: 10
      headers:
        Content-Type: "application/json"
        Authorization: "Bearer $ENV[USAGE_API_TOKEN]"
      operations:
        get_customer_usage:
          method: GET
          path: "/{customer_id}/history"
          path_params:
            - customer_id
          query_params:
            - months
```
</details>

<details>
<summary><b>ML Model Configuration (integrations/ml_generic_example.yaml)</b></summary>

```yaml
ml:
  sources:
    churn_model:
      base_url: "http://localhost:5002/models"
      timeout: 5
      headers:
        Content-Type: "application/json"
      models:
        churn:
          endpoint: "/churn/predict"
          method: "POST"
```
</details>

## Example 3: Product Recommendations with Feast Feature Store

This example demonstrates retrieving customer features from a Feast feature store to generate personalized product recommendations.

**Key Features:**
- Uses Feast feature store for robust feature management
- Combines offline features with real-time context
- Handles both historical behavior and current session data
- Returns personalized product recommendations with relevance scores

### API Endpoint

```
GET /orchestrator/model_scoring/product_recommender/cust_3003
POST /orchestrator/model_scoring/product_recommender/cust_3003
{
  "current_page": "electronics",
  "search_query": "laptop"
}
```

### Sample Response

```json
{
  "customer_id": "cust_3003",
  "recommendations": {
    "products": [
      {"id": "prod_1234", "name": "Ultra Slim Laptop", "category": "laptops", "price": 899.99},
      {"id": "prod_1567", "name": "Premium Laptop Backpack", "category": "accessories", "price": 79.99},
      {"id": "prod_2489", "name": "Wireless Noise-Canceling Headphones", "category": "audio", "price": 249.99}
    ],
    "categories": ["laptops", "accessories", "audio"],
    "relevance_scores": [0.92, 0.85, 0.78]
  },
  "context": {
    "current_page": "electronics",
    "based_on": ["purchase_history", "current_session", "similar_customers"]
  }
}
```

### Configuration Files

<details>
<summary><b>Domain Configuration (domains/model_scoring_product_recommender.yaml)</b></summary>

```yaml
domain_id: model_scoring_product_recommender
description: "Product recommendation model API"

endpoints:
  predict:
    description: "Generate product recommendations using Feast features"
    endpoint_type: "composite"
    
    data_sources:
      # Get customer ID from path parameter
      - name: request_data
        type: direct
        operation: use_request_data
        params:
          customer_id: "$request.path_params.customer_id"
          context: "$request.body"
      
      # Get customer features from Feast
      - name: customer_features
        type: feast
        source_id: default
        operation: get_customer_features
        params:
          entity_id: "$request_data.customer_id"
          feature_refs:
            - "customer:purchase_history"
            - "customer:browsing_behavior"
            - "customer:category_affinity"
            - "customer:price_sensitivity"
      
      # Get additional context features from Feast
      - name: context_features
        type: feast
        source_id: default
        operation: get_context_features
        params:
          entity_id: "$request_data.customer_id"
          context_id: "$request_data.context.session_id"
          feature_refs:
            - "context:current_session"
            - "context:recent_views"
      
      # Call ML model for recommendations
      - name: recommendations
        type: ml
        source_id: recommender_model
        operation: predict
        params:
          features:
            customer_id: "$request_data.customer_id"
            purchase_history: "$customer_features.purchase_history"
            browsing_behavior: "$customer_features.browsing_behavior"
            category_affinity: "$customer_features.category_affinity"
            price_sensitivity: "$customer_features.price_sensitivity"
            current_session: "$context_features.current_session"
            recent_views: "$context_features.recent_views"
            current_page: "$request_data.context.current_page"
            search_query: "$request_data.context.search_query"
    
    # Format the final response
    response_mapping:
      customer_id: "$request_data.customer_id"
      recommendations:
        products: "$recommendations.recommended_products"
        categories: "$recommendations.recommended_categories"
        relevance_scores: "$recommendations.relevance_scores"
      context:
        current_page: "$request_data.context.current_page"
        based_on: "$recommendations.recommendation_factors"
```
</details>

<details>
<summary><b>Feast Configuration (integrations/feast_config.yaml)</b></summary>

```yaml
feast:
  sources:
    default:
      repo_path: "./feature_repo"
      project: "default"
      entity_key_serialization_version: 2
      
      feature_services:
        customer_features:
          features:
            - "customer:purchase_history"
            - "customer:browsing_behavior"
            - "customer:category_affinity"
            - "customer:price_sensitivity"
        
        context_features:
          features:
            - "context:current_session"
            - "context:recent_views"
```
</details>

<details>
<summary><b>ML Model Configuration (integrations/ml_generic_example.yaml)</b></summary>

```yaml
ml:
  sources:
    recommender_model:
      base_url: "http://localhost:5002/models"
      timeout: 5
      headers:
        Content-Type: "application/json"
      models:
        recommender:
          endpoint: "/recommendations/generate"
          method: "POST"
```
</details>

## Request Processing Flow

The orchestrator follows a consistent request handling pattern regardless of the data source:

```
┌─────────────────┐     ┌───────────────────┐     ┌────────────────────┐
│                 │     │                   │     │                    │
│  1. Parse       │────▶│  2. Load          │────▶│  3. Initialize     │
│     Request     │     │     Configuration │     │     Data Adapters  │
│                 │     │                   │     │                    │
└─────────────────┘     └───────────────────┘     └────────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌───────────────────┐     ┌────────────────────┐
│                 │     │                   │     │                    │
│  6. Return      │◀────│  5. Assemble      │◀────│  4. Execute        │
│     Response    │     │     Response      │     │     Data Flow      │
│                 │     │                   │     │                    │
└─────────────────┘     └───────────────────┘     └────────────────────┘
```

### Detailed Processing Steps

<details>
<summary><b>1. Parse Request</b></summary>

- Extract `domain_id` from URL path (e.g., `credit_risk` from `/orchestrator/model_scoring/credit_risk/...`)
- Extract `entity_id` from URL path (e.g., `cust_1001` from `/orchestrator/model_scoring/credit_risk/cust_1001`)
- Extract query parameters from URL
- Parse request body (for POST requests)
</details>

<details>
<summary><b>2. Load Configuration</b></summary>

- Load domain configuration from `config/domains/{domain_id}.yaml`
- Validate the configuration schema
- Process conditional data sources based on request parameters
</details>

<details>
<summary><b>3. Initialize Data Adapters</b></summary>

Based on data source types defined in the configuration:
- `database` → DatabaseClient
- `api` → HttpClient
- `feast` → FeastClient
- `ml` → ModelClient
- `direct` → DirectDataAdapter (for request data)
</details>

<details>
<summary><b>4. Execute Data Flow</b></summary>

- Process data sources in sequence defined in configuration
- For each data source:
  - Prepare parameters by resolving references (e.g., `$customer_data.id`)
  - Execute the operation (database query, API call, ML inference)
  - Store results for use by subsequent data sources
- Data sources can reference data from previous data sources
</details>

<details>
<summary><b>5. Assemble Response</b></summary>

- Apply response mapping defined in configuration
- Transform data based on mapping rules
- Handle nested object structures
- Apply default values for missing data
</details>

<details>
<summary><b>6. Return Response</b></summary>

- Serialize response to JSON
- Set appropriate headers
- Return to client with status code 200
</details>

## Global Application Configuration (config.yaml)

This file contains application-level settings that affect all endpoints:

<details>
<summary><b>View config.yaml example</b></summary>

```yaml
app:
  name: "Orchestrator API Service"
  version: "1.0.0"
  auto_reload: true  # Automatically reload configuration when files change
  
server:
  host: "0.0.0.0"
  port: 8000
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  filename: "orchestrator.log"
```
</details>

## Modifying and Extending the Configuration

The orchestrator API is designed to be extended through configuration rather than code changes. Here's how to add new capabilities:

<table>
<tr>
<td width="33%" valign="top">
<h3>Adding a New Model Endpoint</h3>

1. Create a new YAML file in `config/domains/`:
   ```bash
   touch config/domains/model_scoring_new_model.yaml
   ```

2. Define the domain configuration:
   ```yaml
   domain_id: model_scoring_new_model
   description: "New model API"
   
   endpoints:
     predict:
       # Define endpoint configuration
       # ...
   ```

3. Define data sources and response mapping
</td>

<td width="33%" valign="top">
<h3>Adding a New Database Operation</h3>

1. Edit `config/database.yaml` to add operation:
   ```yaml
   database:
     operations:
       new_operation:
         query: "SELECT * FROM table WHERE id = :id"
         params:
           - id
   ```

2. Reference it from domain configuration:
   ```yaml
   data_sources:
     - name: db_data
       type: database
       operation: new_operation
       params:
         id: "$request.path_params.entity_id"
   ```
</td>

<td width="33%" valign="top">
<h3>Adding a New External API</h3>

1. Edit `config/integrations/api_sources.yaml`:
   ```yaml
   api:
     sources:
       new_api:
         base_url: "http://api.example.com"
         timeout: 5
         operations:
           get_data:
             method: GET
             path: "/{id}"
             path_params:
               - id
   ```

2. Reference it from domain configuration:
   ```yaml
   data_sources:
     - name: api_data
       type: api
       source_id: new_api
       operation: get_data
       params:
         id: "$request.path_params.entity_id"
   ```
</td>
</tr>
</table>

### Configuration Reloading

Configuration changes are loaded dynamically without requiring a service restart (when `auto_reload: true` is set in `config.yaml`). This enables:

- Adding new model endpoints
- Modifying existing endpoints
- Updating database queries
- Changing API connections
- Adjusting response formats

All without downtime or code changes.