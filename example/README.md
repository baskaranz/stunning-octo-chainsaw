# Iris Flower Classification Example

This example demonstrates using the Orchestrator API Service with the classic Iris dataset, showcasing multiple approaches to model integration.

## Overview

The Iris example uses:
- **Database**: SQLite database containing the Iris dataset
- **Models**: scikit-learn classifier trained on the Iris dataset
- **API**:
  - Orchestrator endpoints for configuration-driven access
  - Direct API endpoints with resilient fallback logic

## Features

1. **Multiple Integration Approaches**:
   - Configuration-driven orchestrator endpoints
   - Direct API implementation with resilient fallback strategy
   - Standalone prediction script

2. **Multiple Model Loading Strategies**:
   - HTTP endpoint model (external service)
   - Local artifact model (loading model from filesystem)
   - Rule-based fallback prediction

3. **Complete Example Flow**:
   - Database setup and data loading
   - Model training and deployment
   - API configuration and routing
   - Client request handling

## Components

- **iris_database.py**: Sets up a SQLite database with Iris flower data
- **iris_model_server.py**: Simple Flask server that loads and serves the model
- **create_model.py**: Script to train and save the scikit-learn model
- **run_example.py**: Script to set up and run the example
- **models/iris_model.pkl**: Pre-trained scikit-learn model

## API Endpoints

### Orchestrator Endpoints

These endpoints demonstrate the configuration-driven approach:

```
GET /orchestrator/iris_example/predict/{flower_id}
GET /orchestrator/iris_example/predict_local/{flower_id}
GET /orchestrator/iris_example/compare/{flower_id}
GET /orchestrator/iris_example/samples?limit=5
```

### Direct API Endpoints

These endpoints demonstrate the resilient multi-tier approach:

```
GET /api/iris/{flower_id}
GET /api/iris/samples/{count}
```

## Running the Example

### Step 1: Set up the example

First, make sure you have all dependencies installed:

```bash
pip install -e .
```

Then set up the database and model:

```bash
python example/run_example.py --setup
```

### Step 2: Start the model server

Start the Iris model server:

```bash
python example/iris_model_server.py
```

### Step 3: Start the Orchestrator

Start the main application:

```bash
python main.py
```

### Step 4: Test the endpoints

Using curl:

```bash
# Get a list of samples
curl "http://localhost:8000/orchestrator/iris_example/samples?limit=3"

# Predict using HTTP model
curl "http://localhost:8000/orchestrator/iris_example/predict/1"

# Predict using local model
curl "http://localhost:8000/orchestrator/iris_example/predict_local/1"

# Compare predictions from both models
curl "http://localhost:8000/orchestrator/iris_example/compare/1"

# Direct API endpoint with multi-tier fallback
curl "http://localhost:8000/api/iris/1"

# Get multiple samples with predictions
curl "http://localhost:8000/api/iris/samples/5"
```

## Querying the Database

You can query the SQLite database directly:

```bash
# Connect to the database
sqlite3 example/iris_example.db

# View all tables
.tables

# See the schema
.schema

# Query for specific flower data
SELECT * FROM iris_flowers WHERE id = 1;

# Get all species
SELECT DISTINCT species FROM iris_flowers;

# Get a random sample
SELECT * FROM iris_flowers ORDER BY RANDOM() LIMIT 5;

# Exit SQLite
.quit
```

## Model Loading Strategies

This example demonstrates three approaches to model loading:

1. **HTTP Model**:
   - Traditional approach calling an external model service
   - Model runs as a separate process/service
   - Communication via HTTP requests

2. **Local Artifact Model**:
   - Model is loaded directly from the filesystem
   - Uses the saved model file for predictions
   - No need for a separate service

3. **Direct API Implementation**:
   - Implemented as a direct FastAPI endpoint
   - Multi-tier fallback strategy:
     - First tries the HTTP model service
     - Then tries to load a local model file
     - Finally falls back to rule-based prediction if both methods fail
   - More resilient and handles failure scenarios gracefully

## Configuration Structure

The Iris example is configured as a domain within the orchestrator:

```
config/domains/iris_example.yaml            # Main domain config
config/domains/iris_example/database.yaml   # Database operations
config/domains/iris_example/integrations/ml_config.yaml # ML model config
```

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