# Loan Prediction Example

This example demonstrates how to use the Orchestrator API Service to create a loan approval prediction service that integrates data from multiple sources.

## Overview

The loan prediction example showcases:

1. Retrieving applicant data from a database
2. Sending that data to an ML model for prediction
3. Combining and formatting the results

## Components

- **Database**: SQLite database containing applicant information, financial data, and loan history
- **ML Service**: A mock ML service that predicts loan approval probability
- **Orchestrator API**: Configures and manages data flow between components

## Example Files

- `setup_database.py`: Creates and populates the example database
- `mock_ml_service.py`: Simple HTTP server that simulates an ML prediction service
- `get_loan_prediction.py`: Client script to query the orchestration API
- `run_complete_example.py`: End-to-end example that doesn't require starting services separately

## Configuration

The loan prediction example uses the following configuration files:

- `config/database.yaml`: Database connection settings
- `config/domains/loan_prediction.yaml`: Domain-specific data flow configuration
- `config/integrations/ml.yaml`: ML service connection settings

## Running the Example

### Option 1: Running the Complete Example (Recommended)

For a simple demonstration:

```bash
python examples/loan_prediction/run_complete_example.py --setup-db
```

This will:
1. Set up the database
2. Run the entire prediction flow in-process
3. Display the results

### Option 2: Running with Separate Services

For a more realistic setup with actual services:

1. First, set up the database:
   ```bash
   python examples/loan_prediction/setup_database.py
   ```

2. Start the mock ML service:
   ```bash
   python examples/loan_prediction/simple_ml_server.py 5001
   ```

3. In a new terminal, start the orchestrator API service:
   ```bash
   ORCHESTRATOR_CONFIG_PATH=examples/loan_prediction/config python main.py
   ```

4. In a new terminal, run the client:
   ```bash
   python examples/loan_prediction/get_loan_prediction.py app_1001
   ```

## Available Test Applicants

The example database includes several test applicants:

- `app_1001`: Alex Johnson (Good credit, high approval probability)
- `app_1002`: Sarah Williams (Excellent credit, very high approval probability)
- `app_1003`: Michael Brown (Fair credit, medium approval probability)
- `app_1004`: Emily Davis (Poor credit, low approval probability)
- `app_1005`: David Wilson (Bad credit, very low approval probability)

## Extending the Example

You can extend this example in several ways:

1. Add more features to the applicant data model
2. Create a more sophisticated ML prediction model
3. Add additional data sources (e.g., credit bureau API)
4. Implement a front-end UI to interact with the loan prediction service