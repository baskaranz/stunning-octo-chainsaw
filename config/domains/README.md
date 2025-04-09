# Domain Configurations

This directory contains all the domain-specific configurations for the Orchestrator API Service. Each domain represents a logical group of related functionality that the orchestrator can process.

## Domain Organization

Each domain follows this organization:

```
domains/
├── domain_name.yaml              # Main domain configuration with endpoints
├── domain_name/                  # Domain-specific resources
│   ├── database.yaml             # Database configuration for this domain
│   └── integrations/             # Integration configurations
│       ├── api_sources.yaml      # API sources for this domain
│       ├── feast_config.yaml     # Feast feature store config for this domain
│       └── ml_config.yaml        # ML model configurations for this domain
```

## Available Domains

The following domains are currently configured:

### Iris Example

- **Domain ID**: `iris_example`
- **Description**: Iris flower classification example using sklearn model
- **Endpoints**:
  - `/orchestrator/iris_example/predict/{flower_id}` - Predict species using HTTP model
  - `/orchestrator/iris_example/predict_local/{flower_id}` - Predict using locally loaded model
  - `/orchestrator/iris_example/compare/{flower_id}` - Compare predictions from both models
  - `/orchestrator/iris_example/samples` - Get random iris samples
  - `/orchestrator/iris_example/species` - Get all iris species

### Model Scoring Examples

- **Domain IDs**: 
  - `model_scoring_credit_risk`
  - `model_scoring_product_recommender`
  - `model_scoring_loan_pred`
  - `model_scoring_churn_pred`
- **Description**: Example model scoring domains for different use cases
- **Endpoints**: Various model scoring endpoints, see individual domain files for details

### Model Loading Examples

- **Domain ID**: `model_loading_examples`
- **Description**: Demonstrates various model loading strategies
- **Features**:
  - HTTP API models (traditional approach)
  - Local artifact models (load models from filesystem)
  - Docker models (run models in Docker containers)
  - ECR models (pull and run models from Amazon ECR)

## Adding a New Domain

To add a new domain:

1. Create a domain configuration file: `domains/your_domain.yaml`
2. Create a domain directory: `domains/your_domain/`
3. Add domain-specific configurations:
   - `domains/your_domain/database.yaml`
   - `domains/your_domain/integrations/api_sources.yaml`
   - `domains/your_domain/integrations/ml_config.yaml`
   - etc.
4. Restart the orchestrator service or use the reload endpoint

The orchestrator will automatically discover and load all domain configurations from this directory.