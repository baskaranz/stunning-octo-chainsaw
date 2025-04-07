# Generic Orchestrator API Example

This example demonstrates how to use the generic orchestrator API for model scoring with different data sources and model types.

## Overview

The generic orchestrator API provides a unified interface for model scoring that can be configured without code changes. This example shows:

1. How to configure and use two different model scoring endpoints:
   - Credit risk scoring model
   - Product recommendation model

2. How to retrieve data from multiple sources:
   - Database tables
   - Request parameters
   - External APIs

3. How to call ML services with the appropriate request format

## Components

### Database Layer
- SQLite database with sample customer data, products, and transactions
- Tables for credit history, payment behavior, and product preferences

### ML Service Layer
- Mock HTTP servers simulating two different ML models:
  - Credit risk model: Predicts default probability
  - Recommendation model: Suggests products based on user behavior

### Configuration Layer
- YAML files defining the data flow for each model
- Response mapping configurations
- Feature mappings and transformations

## Data Flow Architecture

```
┌──────────────┐       ┌─────────────────┐       ┌──────────────┐
│              │       │                 │       │              │
│   Database   │───────▶   Orchestrator  │───────▶   ML Model   │
│              │       │                 │       │              │
└──────────────┘       └─────────────────┘       └──────────────┘
       ▲                        ▲
       │                        │
       │                ┌───────────────┐
       └────────────────┤  HTTP Request │
                        └───────────────┘
```

## Running the Example

### Option 1: All-in-One Setup (Recommended)

The simplest way to run the example is with the all-in-one script:

```bash
python examples/generic_orchestrator/run_example.py
```

This script will:
1. Create and populate the database
2. Start the mock ML services
3. Configure the orchestrator API
4. Run test API calls
5. Keep the services running for you to try your own queries

When you're done, press Ctrl+C to stop all services.

### Option 2: Manual Setup

If you prefer to run each component separately:

1. Set up the database:
   ```bash
   python examples/generic_orchestrator/setup_database.py
   ```

2. Start the mock ML services:
   ```bash
   python examples/generic_orchestrator/mock_ml_services.py
   ```

3. Start the orchestrator API:
   ```bash
   python main.py
   ```

4. Call the API endpoints with curl:
   ```bash
   # Credit risk scoring by customer ID
   curl "http://localhost:8000/orchestrator/model_scoring/credit_risk/cust_1001"
   
   # Product recommendations with additional context
   curl -X POST "http://localhost:8000/orchestrator/model_scoring/product_recommender/cust_1002" \
     -H "Content-Type: application/json" \
     -d '{"current_page": "electronics", "recent_searches": ["laptop", "headphones"]}'
   ```

5. Or use the provided client script:
   ```bash
   # Credit risk score for a customer
   python examples/generic_orchestrator/api_client.py credit-risk --id cust_1001
   
   # Product recommendations with both ID and context
   python examples/generic_orchestrator/api_client.py product-recommender --id cust_1002 \
     --context "current_page=electronics,recent_searches=laptop|headphones"
   ```

## Model Endpoints

### Credit Risk Scoring

The credit risk model provides a risk assessment for a customer:

- **Endpoint**: `/orchestrator/model_scoring/credit_risk/{customer_id}`
- **Method**: GET
- **Data Sources**:
  - Customer profile from database
  - Credit history from database
  - Payment behavior from database
- **Output**: Risk score, risk tier, key factors, and recommended actions

Example response:
```json
{
  "customer_id": "cust_1001",
  "name": "Alice Johnson",
  "risk_score": {
    "score": 87,
    "risk_tier": "Low",
    "default_probability": 0.15,
    "confidence": 0.92
  },
  "credit_profile": {
    "credit_score": 720,
    "debt_to_income": 0.32,
    "payment_history_score": 0.95
  },
  "key_factors": [
    {"factor": "consistent_payment_history", "impact": 0.35},
    {"factor": "long_customer_relationship", "impact": 0.28},
    {"factor": "recent_credit_inquiry", "impact": -0.12}
  ],
  "recommended_actions": [
    {"action": "pre_approve_credit_line_increase", "confidence": 0.88},
    {"action": "offer_premium_product", "confidence": 0.76}
  ]
}
```

### Product Recommendation

The product recommendation model suggests products based on customer preferences and behavior:

- **Endpoint**: `/orchestrator/model_scoring/product_recommender/{customer_id}`
- **Methods**: GET, POST
- **Data Sources**:
  - Customer profile from database
  - Purchase history from database
  - Current browse context from request
- **Output**: List of recommended products with relevance scores

Example response:
```json
{
  "customer_id": "cust_1002",
  "recommendations": [
    {
      "product_id": "prod_5009",
      "name": "Wireless Headphones",
      "relevance_score": 0.95,
      "price_tier": "premium",
      "category": "electronics"
    },
    {
      "product_id": "prod_3012",
      "name": "Bluetooth Speaker",
      "relevance_score": 0.87,
      "price_tier": "mid-range",
      "category": "electronics"
    },
    {
      "product_id": "prod_4104",
      "name": "Laptop Sleeve",
      "relevance_score": 0.72,
      "price_tier": "budget",
      "category": "accessories"
    }
  ],
  "context": {
    "current_page": "electronics",
    "based_on": ["purchase_history", "current_session", "similar_customers"]
  }
}
```

## Implementation Files

- `run_example.py`: All-in-one script to set up and run the example
- `database_model.py`: Database schema and sample data
- `mock_ml_services.py`: Simulates the ML models
- `database_extensions.py`: Database client extensions for the example
- `api_client.py`: Client-side example of API usage

### Configuration Files
- `config/domains/model_scoring_credit_risk.yaml`: Credit risk model configuration
- `config/domains/model_scoring_product_recommender.yaml`: Product recommendation configuration
- `config/integrations/ml_generic_example.yaml`: ML service connection settings

## How It Works

The orchestrator works by:

1. Reading the configuration for the requested model
2. Fetching data from the configured sources
3. Mapping the data to the format expected by the ML model
4. Calling the ML model with the prepared features
5. Mapping the response to the defined output format

All of this happens without needing to write model-specific code in the API service itself, making it easy to add new models by simply adding new configuration files.

## Adding Your Own Model

To add a new model to the orchestrator:

1. Create a configuration file in `config/domains/model_scoring_your_model.yaml`
2. Define the data sources, feature mappings, and response format
3. Implement any necessary database methods (if not already available)
4. Restart the application to load the new configuration

No code changes are required to the orchestrator API itself.