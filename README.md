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
  - Databases (for internal feature retrieval)
  - External APIs
  - Feature stores (Feast)
  - ML model services
- **Multiple Model Loading Strategies**:
  - HTTP API models (traditional approach)
  - Local artifact models (load models from filesystem)
  - Docker container models (run models in Docker)
  - ECR repository models (pull and run models from AWS ECR)
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

The service uses a configuration-driven approach with files located in the `config/` directory:

- `config.yaml`: Global application settings
- `database.yaml`: Database connection settings
- `domains/`: Domain-specific endpoint configurations (one file per domain)
- `integrations/`: External system configurations

**For Example Configurations:** See the [example/config](example/config/) directory for complete sample configurations that demonstrate different data source patterns.

### Endpoint Configuration

The Orchestrator API Service supports configuring different types of endpoints through YAML configuration files. You can define endpoints that:

1. **Database to ML Model**: Retrieve features from database tables and score with ML models
   ```yaml
   endpoints:
     predict:
       description: "Predict credit risk using customer data"
       endpoint_type: "composite"
       data_sources:
         - name: customer_data
           type: database
           operation: get_customer
           params:
             customer_id: "$request.path_params.entity_id"
         
         - name: risk_prediction
           type: ml
           source_id: credit_model
           operation: predict
           params:
             features:
               credit_score: "$customer_data.credit_score"
               income: "$customer_data.annual_income"
       
       response_mapping:
         customer_id: "$customer_data.customer_id"
         risk_score: "$risk_prediction.score"
         risk_tier: "$risk_prediction.risk_tier"
   ```

2. **External API to ML Model**: Call external APIs for data and pass to ML models
   ```yaml
   endpoints:
     predict:
       description: "Predict churn using external API data"
       endpoint_type: "composite"
       data_sources:
         - name: customer_profile
           type: api
           source_id: customer_api
           operation: get_customer_profile
           params:
             customer_id: "$request.path_params.entity_id"
         
         - name: churn_prediction
           type: ml
           source_id: churn_model
           operation: predict
           params:
             features:
               tenure: "$customer_profile.tenure"
               monthly_charges: "$customer_profile.monthly_charges"
       
       response_mapping:
         customer_id: "$customer_profile.id"
         churn_probability: "$churn_prediction.probability"
         risk_level: "$churn_prediction.risk_level"
   ```

3. **Feature Store to ML Model**: Fetch features from Feast and use for model predictions
   ```yaml
   endpoints:
     predict:
       description: "Generate recommendations using Feast features"
       endpoint_type: "composite"
       data_sources:
         - name: customer_features
           type: feast
           source_id: default
           operation: get_customer_features
           params:
             entity_id: "$request.path_params.entity_id"
             feature_refs:
               - "customer:purchase_history"
               - "customer:category_affinity"
         
         - name: recommendations
           type: ml
           source_id: recommender_model
           operation: predict
           params:
             features:
               purchase_history: "$customer_features.purchase_history"
               category_affinity: "$customer_features.category_affinity"
       
       response_mapping:
         customer_id: "$request.path_params.entity_id"
         recommendations: "$recommendations.recommended_products"
         relevance_scores: "$recommendations.relevance_scores"
   ```

4. **Multi-Source ML Model**: Combine data from multiple sources for complex model scoring
   ```yaml
   endpoints:
     predict:
       description: "Generate loan approval prediction from multiple sources"
       endpoint_type: "composite"
       data_sources:
         # Get customer profile from database
         - name: applicant
           type: database
           operation: get_applicant
           params:
             applicant_id: "$request.path_params.entity_id"
         
         # Get feature data from feature store
         - name: behavior_features
           type: feast
           source_id: default
           operation: get_features
           params:
             entity_id: "$request.path_params.entity_id"
         
         # Get external credit score from API
         - name: credit_data
           type: api
           source_id: credit_api
           operation: get_credit_score
           params:
             applicant_id: "$request.path_params.entity_id"
         
         # Score the loan with ML model
         - name: loan_prediction
           type: ml
           source_id: loan_model
           operation: predict
           params:
             features:
               age: "$applicant.age"
               income: "$applicant.annual_income"
               payment_history: "$behavior_features.payment_history"
               credit_score: "$credit_data.score"
       
       response_mapping:
         applicant_id: "$applicant.applicant_id"
         approval_probability: "$loan_prediction.probability"
         decision: "$loan_prediction.decision"
         suggested_interest_rate: "$loan_prediction.interest_rate"
   ```

For more detailed configuration examples, see the [Example Config README](example/config/README.md).

## Examples

The repository includes examples that demonstrate:

1. **Model Scoring**: Shows integration with ML services using data from databases:
   - Credit risk scoring model
   - Product recommendation model
   - Loan prediction model

2. **Multi-Source Data Flow**: Demonstrates retrieving and combining data from:
   - Database tables (for features)
   - Request parameters
   - External APIs
   - Feature stores

3. **Model Loading Strategies**: Shows different ways to load and run ML models:
   - HTTP API models (calling external services)
   - Local artifact models (loading from filesystem)
   - Docker container models (running in Docker)
   - ECR repository models (pulling from AWS ECR)

For more details, see the [Example README](example/README.md) and [Model Loading Documentation](docs/model_loading.md).

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