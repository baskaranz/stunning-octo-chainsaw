# Iris Example with Orkestra CLI

This README provides a step-by-step guide for running the Iris flower classification example using the Orkestra CLI.

## Overview

The Iris example demonstrates a machine learning prediction workflow using the Orkestra framework with multiple data sources and prediction strategies:

- HTTP model service as primary prediction method
- Local model file as secondary fallback
- Rule-based prediction as tertiary fallback
- Feature retrieval from database and feature store (Feast)

## Prerequisites

- Python 3.9+
- Orkestra library installed (`pip install -e .` from project root)

## Quick Start

The fastest way to run the Iris example:

```bash
# 1. Set up the example (creates database and copies config files)
python example/run_iris_example.py --setup

# 2. Start the model server
python example/run_iris_example.py --server

# 3. In another terminal, start the Orkestra service with the CLI
orkestra run --config-path ./config

# 4. Test the endpoints
python example/run_iris_example.py --test-orchestrator
```

## Step-by-Step Guide

### 1. Setup the Example Environment

Set up the example database and configuration files:

```bash
python example/run_iris_example.py --setup
```

This command:
- Creates the Iris SQLite database with sample data
- Copies configuration files to the main config directory
- Sets up the necessary directory structure

### 2. Start the Iris Model Server

Start the Flask-based model server:

```bash
python example/run_iris_example.py --server
```

This starts a model server on port 8502 (you can specify a different port with `--model-port PORT`).

### 3. Start the Orkestra Service

In a new terminal, start the Orkestra service using the CLI:

```bash
# Basic usage
orkestra run --config-path ./config

# With development reload enabled
orkestra run --config-path ./config --reload

# With custom host and port
orkestra run --host 127.0.0.1 --port 8080 --config-path ./config
```

### 4. Testing the Endpoints

After both the model server and Orkestra service are running, you can test the endpoints:

```bash
# Test the orchestrator endpoints
python example/run_iris_example.py --test-orchestrator

# Test the model comparison endpoint
python example/run_iris_example.py --test-comparison

# Check if the Orkestra service loaded the Iris domain
python example/run_iris_example.py --check-orchestrator
```

## Available Endpoints

The Iris example exposes several endpoints:

- `/orchestrator/iris_example/predict/{flower_id}` - Predict species using HTTP model
- `/orchestrator/iris_example/predict_local/{flower_id}` - Predict using locally loaded model
- `/orchestrator/iris_example/predict_feast/{flower_id}` - Predict using Feast feature store
- `/orchestrator/iris_example/compare/{flower_id}` - Compare HTTP and local model predictions
- `/orchestrator/iris_example/compare_all/{flower_id}` - Compare all prediction methods
- `/orchestrator/iris_example/samples?limit=5` - Get random iris samples
- `/orchestrator/iris_example/species` - Get all iris species

## Creating Your Own Project

You can use Orkestra CLI to create a new project based on this example:

```bash
# Initialize a new project
orkestra init my-new-project

# Navigate to the new project
cd my-new-project

# Start the service
orkestra run --config-path ./config --reload
```

## Configuration Structure

The Iris example uses the following configuration files:

- `config/domains/iris_example.yaml` - Main domain configuration with endpoint definitions
- `config/domains/iris_example/database.yaml` - Database configuration
- `config/domains/iris_example/integrations/ml_config.yaml` - ML model configuration

## Advanced Usage

### Custom Model Port

```bash
python example/run_iris_example.py --server --model-port 8503
```

### Custom API Port

```bash
# Start the orchestrator on a custom port
orkestra run --port 8001 --config-path ./config

# Test with the custom port
python example/run_iris_example.py --test-orchestrator --api-port 8001
```

## Troubleshooting

If the endpoints aren't working:

1. Check if the orchestrator loaded the Iris domain:
   ```bash
   python example/run_iris_example.py --check-orchestrator
   ```

2. Verify the model server is running:
   ```bash
   curl http://localhost:8502/health
   ```

3. Check the database is properly set up:
   ```bash
   ls -l example/iris_example.db
   ```

4. Restart both services if needed