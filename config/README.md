# Configuration Architecture

This document explains how the various configuration files in the Orchestrator API Service work together to define endpoints, data flows, and integrations.

## Configuration Overview

The Orchestrator API Service uses a hierarchical configuration structure to define:
- Global application settings
- Database connections and operations
- External API endpoints
- Feature store configurations
- ML model integrations
- Domain-specific API endpoints

## Configuration File Structure

```
config/
├── config.yaml                 # Global application settings
├── database.yaml               # Database connections and queries
├── domains/                    # Endpoint definitions by domain
│   ├── customers.yaml          # Customer domain endpoints
│   ├── model_scoring_credit_risk.yaml
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
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────┬─────────────┴─────────────┬─────────────────────┐
│    database.yaml        │    domains/*.yaml         │  integrations/*.yaml│
│                         │                           │                     │
│ ┌─────────────────────┐ │ ┌─────────────────────┐  │ ┌─────────────────┐ │
│ │Database Connections │ │ │Endpoint Definitions │  │ │External Systems │ │
│ │  - source_id        │◄┼─┤  - data_sources     │──┼►│  - source_id    │ │
│ │  - connection_string│ │ │  - endpoint_type    │  │ │  - base_url     │ │
│ └─────────────────────┘ │ └─────────────────────┘  │ └─────────────────┘ │
│                         │                           │                     │
│ ┌─────────────────────┐ │ ┌─────────────────────┐  │ ┌─────────────────┐ │
│ │Database Operations  │ │ │Request Parameters   │  │ │API Operations   │ │
│ │  - operation name   │◄┼─┤  - params mapping   │  │ │  - methods      │ │
│ │  - SQL query        │ │ │  - validation       │  │ │  - endpoints    │ │
│ └─────────────────────┘ │ └─────────────────────┘  │ └─────────────────┘ │
│                         │                           │                     │
│                         │ ┌─────────────────────┐  │ ┌─────────────────┐ │
│                         │ │Response Mapping     │  │ │ML Models        │ │
│                         │ │  - field mapping    │  │ │  - models       │ │
│                         │ │  - transformations  │  │ │  - endpoints    │ │
│                         │ └─────────────────────┘  │ └─────────────────┘ │
└─────────────────────────┴───────────────────────┬──┴─────────────────────┘
                                                  │
                                                  ▼
     ┌──────────────────────────────────────────────────────────────────┐
     │                    Dynamic API Endpoints                          │
     │                                                                   │
     │  - /api/customer/{customer_id}                                   │
     │  - /orchestrator/model_scoring/credit_risk/{customer_id}         │
     │  - /orchestrator/model_scoring/product_recommender/{customer_id} │
     └──────────────────────────────────────────────────────────────────┘
```

## Configuration Flow Example

Here's an example of how the configurations connect for a model scoring endpoint:

1. **User Request**:
   - Request hits: `/orchestrator/model_scoring/credit_risk/cust_1001`

2. **Configuration Loading**:
   - `app/config/endpoint_config_manager.py` loads domain config: `domains/model_scoring_credit_risk.yaml`

3. **Data Source Resolution**:
   - Domain config references data sources with `source_id` values
   - Database sources reference connections from `database.yaml`
   - ML sources reference models from `integrations/ml_generic_example.yaml`

4. **Parameter Mapping**:
   - Request parameters (`cust_1001`) mapped to data source parameters
   - Database queries executed with parameters from `database.yaml`
   - API/ML calls made with configuration from integration files

5. **Response Assembly**:
   - Results from multiple sources assembled according to `response_mapping`
   - Final response returned to the client

## References Between Config Files

### From Domains to Database

In `domains/model_scoring_credit_risk.yaml`:
```yaml
data_sources:
  - name: customer_data
    type: database
    source_id: default  # References a database in database.yaml
    operation: get_customer  # References a query in database.yaml
```

In `database.yaml`:
```yaml
database:
  sources:
    default:  # The source_id referenced above
      connection_string: "sqlite:///customer360.db"
  
  operations:
    get_customer:  # The operation referenced above
      query: "SELECT * FROM customers WHERE customer_id = :customer_id"
```

### From Domains to ML Models

In `domains/model_scoring_credit_risk.yaml`:
```yaml
data_sources:
  - name: risk_prediction
    type: ml
    source_id: credit_model  # References an ML model in integrations/ml_generic_example.yaml
    operation: predict
```

In `integrations/ml_generic_example.yaml`:
```yaml
ml:
  sources:
    credit_model:  # The source_id referenced above
      base_url: "http://localhost:5002/models"
      models:
        credit_risk:
          endpoint: "/credit-risk/predict"
```

## Complete Configuration Flow Example

The following shows a complete end-to-end configuration flow for a credit risk scoring model:

### 1. API Request

```
GET /orchestrator/model_scoring/credit_risk/cust_1001
```

### 2. Domain Configuration (domains/model_scoring_credit_risk.yaml)

```yaml
domain_id: model_scoring_credit_risk
description: "Credit risk assessment model API"

endpoints:
  predict:
    description: "Predict credit risk using customer data"
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

### 3. Database Configuration (database.yaml)

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

### 4. ML Service Configuration (integrations/ml_generic_example.yaml)

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

### 5. Application Configuration (config.yaml)

```yaml
app:
  name: "Orchestrator API Service"
  version: "1.0.0"
  auto_reload: true
  
server:
  host: "0.0.0.0"
  port: 8000
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  filename: "orchestrator.log"
```

### 6. Request Processing Flow

1. Request path parsed to extract domain (`model_scoring_credit_risk`) and entity ID (`cust_1001`)
2. Endpoint configuration loaded from domain file
3. Data source adapters initialized for each source type:
   - DatabaseClient for database operations
   - ModelClient for ML operations
4. Data Orchestrator executes the data flow:
   - Database queries executed for customer and credit data
   - Features prepared and sent to ML model
   - Response assembled according to mapping
5. Final JSON response returned to client

## Making Changes to Configuration

When adding or modifying endpoints:

1. **For a new domain**:
   - Create a new YAML file in `config/domains/`
   - Define endpoints, data sources, and response mappings

2. **For a new database operation**:
   - Add the operation to `config/database.yaml`
   - Reference it from domain files

3. **For a new external integration**:
   - Add the source to the appropriate file in `config/integrations/`
   - Reference it from domain files

Configuration changes are dynamically loaded without service restart (when the `auto_reload` setting is enabled).