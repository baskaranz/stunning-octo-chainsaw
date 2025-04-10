# Direct Iris API Implementation

This document describes the direct Iris API implementation that provides a resilient approach to making predictions for the Iris flower classification example.

## Overview

The Direct Iris API is implemented as a standalone FastAPI endpoint that:
- Retrieves iris data from the database
- Makes predictions using a multi-tier fallback strategy
- Provides both individual and batch prediction endpoints
- Handles errors gracefully with appropriate HTTP status codes

## Endpoints

### 1. Get Prediction for a Single Flower

```
GET /api/iris/{flower_id}
```

**Path Parameters:**
- `flower_id` (integer, required): The ID of the iris flower to make a prediction for.

**Response:**
```json
{
  "flower_id": 1,
  "features": {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  },
  "actual_species": "setosa",
  "prediction": {
    "class_name": "setosa",
    "probabilities": {
      "setosa": 0.95,
      "versicolor": 0.04,
      "virginica": 0.01
    }
  },
  "prediction_method": "http"
}
```

### 2. Get Predictions for Multiple Samples

```
GET /api/iris/samples/{count}
```

**Path Parameters:**
- `count` (integer, optional, default=5): The number of random samples to retrieve and make predictions for.

**Response:**
```json
[
  {
    "flower_id": 1,
    "features": { ... },
    "actual_species": "setosa",
    "prediction": { ... },
    "prediction_method": "http"
  },
  ...
]
```

## Multi-tier Fallback Strategy

The API uses a three-tier fallback strategy for predictions:

1. **HTTP Model**: First attempts to call the ML server running on port 8502.
2. **Local Model**: If the HTTP model is unavailable, tries to load and use a local model file from the filesystem.
3. **Rule-based Prediction**: If both methods fail, falls back to a simple rule-based prediction algorithm based on Fisher's original paper.

This strategy ensures that the API remains operational even when the ML service is down or the model file is missing.

## Implementation Details

The implementation is located in:
- `/app/api/controllers/iris_controller.py`: Main controller with endpoints and prediction logic
- `/app/api/routes.py`: Router configuration that adds the iris controller

The standalone `iris_prediction.py` script in the root directory provides a simplified version of the prediction logic that can be used for testing outside the FastAPI application.

## Usage Example

```bash
# Get prediction for flower with ID 1
curl "http://localhost:8000/api/iris/1"

# Get predictions for 5 random samples
curl "http://localhost:8000/api/iris/samples/5"
```

## Error Handling

The API handles errors gracefully with appropriate HTTP status codes:

- **404 Not Found**: Returned when the database file or the requested flower ID cannot be found.
- **500 Internal Server Error**: Returned for unexpected errors during processing.

Each error response includes a detail message explaining the cause of the error.