# Iris Flower Classification Example

This example demonstrates using the Orchestrator API Service with the classic Iris dataset, showcasing:

1. Database to ML pattern
2. Multiple model loading strategies:
   - HTTP endpoint model
   - Local artifact model (loading model from filesystem)
3. Comparison of predictions from different model sources

## Overview

The example uses:
- **Database**: SQLite database containing the Iris dataset
- **Models**: scikit-learn classifier trained on the Iris dataset
- **API**: Orchestrator endpoints to query the database and make predictions

## Components

- **iris_database.py**: Sets up a SQLite database with Iris flower data
- **iris_model_server.py**: Simple Flask server that loads and serves the model
- **run_iris_example.py**: Script to set up and run the example

## Configuration

The configuration demonstrates:
- Database operations for retrieving Iris data
- ML model configuration with two loading strategies:
  - HTTP model (calling an external API)
  - Local artifact model (loading model from filesystem)
- Multiple endpoints that showcase different patterns

## Running the Example

### Step 1: Set up the example

First, make sure you have all dependencies installed:

```bash
pip install -e .
```

### Step 2: Start the model server

Start the Iris model server in one terminal:

```bash
python example/iris_example/run_iris_example.py --server
```

### Step 3: Start the Orchestrator

Start the Orchestrator API Service in another terminal:

```bash
python main.py --config example/iris_example/config
```

### Step 4: Test the endpoints

You can test the endpoints using the provided script:

```bash
# Test the direct model endpoint
python example/iris_example/run_iris_example.py --test-direct

# Test the orchestrator endpoint
python example/iris_example/run_iris_example.py --test-orchestrator

# Test the comparison endpoint
python example/iris_example/run_iris_example.py --test-comparison
```

Or using curl:

```bash
# Get a list of samples
curl "http://localhost:8000/orchestrator/iris_example/samples?limit=3"

# Predict using HTTP model
curl "http://localhost:8000/orchestrator/iris_example/predict/1"

# Predict using local model
curl "http://localhost:8000/orchestrator/iris_example/predict_local/1"

# Compare predictions from both models
curl "http://localhost:8000/orchestrator/iris_example/compare/1"
```

## Understanding the Data Flow

1. The client makes a request to the Orchestrator API
2. The Orchestrator retrieves Iris flower data from the database
3. The features are sent to the ML model for prediction
4. The model returns a predicted species
5. The Orchestrator combines the data and prediction into a response

## Example Response

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
    "class_index": 0,
    "class_name": "setosa",
    "probabilities": {
      "setosa": 1.0,
      "versicolor": 0.0,
      "virginica": 0.0
    }
  }
}
```

## Model Loading Strategies

This example demonstrates two approaches to model loading:

1. **HTTP Model**:
   - Traditional approach calling an external model service
   - Model runs as a separate process/service
   - Communication via HTTP requests

2. **Local Artifact Model**:
   - Model is loaded directly from the filesystem
   - Orchestrator starts the model server process
   - No need for a separate deployment

The comparison endpoint shows that both approaches produce the same results, while giving flexibility in deployment options.