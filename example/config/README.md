# Example Configurations

This directory contains example configurations for the orchestrator service, demonstrating how to set up model scoring endpoints for different data sources:

## Directory Structure

```
config/
├── config.yaml                 # Global application settings
├── database.yaml               # Database connections and queries
├── domains/                    # Endpoint definitions for each model
│   ├── model_scoring_credit_risk.yaml            # Database → ML example
│   ├── model_scoring_churn_pred.yaml             # API → ML example 
│   ├── model_scoring_product_recommender.yaml    # Feast → ML example
│   └── model_scoring_loan_pred.yaml              # Mixed source example
└── integrations/               # External system connections
    ├── ml_generic_example.yaml # ML model configurations
    └── mock_services.yaml      # Mock service settings
```

## Model Scoring Examples

### 1. Credit Risk Model (Database → ML)
- **Configuration**: `domains/model_scoring_credit_risk.yaml`
- **Data Source**: Customer and credit profile from database
- **Description**: Uses SQL queries to retrieve customer data, then scores it with a credit risk model
- **Endpoint**: `/orchestrator/model_scoring/credit_risk/{customer_id}`

### 2. Churn Prediction Model (API → ML)
- **Configuration**: `domains/model_scoring_churn_pred.yaml`
- **Data Source**: Customer profile and usage data from external APIs
- **Description**: Calls multiple external APIs to gather customer data, then scores it with a churn prediction model
- **Endpoint**: `/orchestrator/model_scoring/churn_pred/{customer_id}`

### 3. Product Recommender (Feast → ML)
- **Configuration**: `domains/model_scoring_product_recommender.yaml`
- **Data Source**: Customer features from Feast feature store
- **Description**: Retrieves feature vectors from Feast, combines with session context, then generates recommendations
- **Endpoint**: `/orchestrator/model_scoring/product_recommender/{customer_id}`

## Using This Configuration

These configurations are designed to be used with the orchestrator service as part of your own application.
In a real-world deployment:

1. Each specific model scoring endpoint would have its own domain configuration
2. The core orchestrator service would be a dependency
3. Your application would provide configuration files like these

## Customizing for Your Needs

To adapt these examples for your own use:

1. Copy the relevant configuration files to your project
2. Modify the database operations to match your schema
3. Update the ML model endpoints to point to your actual model services
4. Adjust the feature mappings to match your data model

See the [core documentation](../../config/README.md) for more details on configuration options.