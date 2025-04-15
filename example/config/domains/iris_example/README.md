# Iris Example with Feast Integration

This example demonstrates how to use Feast as a feature store for ML model prediction with the orchestrator service, including an automatic fallback to database queries when Feast is unavailable.

## Overview

The example shows several patterns for obtaining features for ML model predictions:

1. **Database → ML**: The traditional pattern of querying a database for features and sending them to an ML model
2. **Feast → ML (with database fallback)**: Using Feast feature store to retrieve features, with automatic fallback to database if Feast is unavailable
3. **Local Model**: Using a locally-loaded model (instead of a remote model service)

## Configuration Files

- `iris_example.yaml`: Domain configuration with endpoint definitions
- `database.yaml`: Database configuration with SQL queries
- `integrations/feast_config.yaml`: Feast configuration with feature definitions and database fallback mapping

## Endpoints

### 1. predict

Standard Database → ML pattern endpoint.

### 2. predict_feast

Uses the Feast → ML pattern with database fallback:
1. Gets features from Feast feature store
2. If Feast is unavailable or fails, automatically falls back to database 
3. Uses retrieved features to get predictions from ML model

### 3. compare_all

Compares all three patterns:
1. Gets features from both sources (database and Feast)
2. Gets predictions using all three patterns 
3. Returns a comparison of features and predictions

## Database Fallback Mechanism

The database fallback mechanism is configured in `integrations/feast_config.yaml`:

```yaml
database_fallback:
  enabled: true
  table: "iris_flowers"
  entity_key: "id"
  mapping:
    "iris:sepal_length": "sepal_length"
    "iris:sepal_width": "sepal_width"
    "iris:petal_length": "petal_length"
    "iris:petal_width": "petal_width"
```

This maps Feast feature names to database column names, allowing seamless fallback when Feast is unavailable.

## Implementation

The Feast client (`app/adapters/feast/feast_client.py`) implements:

1. Logic to check if Feast is available
2. Fallback to database queries when Feast is unavailable
3. Mapping between Feast features and database columns

## Running the Example

To run this example:

1. Start the orchestrator service with the Iris configuration
2. Call the endpoints to see the different patterns in action

Even if Feast is not installed or available, the system will automatically fall back to using the database.