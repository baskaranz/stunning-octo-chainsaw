# Loan Prediction Example

This guide explains how to use the Orchestrator API Service to build a loan approval prediction service that integrates data from a database and machine learning model.

## Overview

The loan prediction example demonstrates a common real-world scenario: integrating customer data with ML models to automate lending decisions. This showcase:

1. Retrieving applicant data from a SQLite database
2. Sending this data to an ML model for approval prediction
3. Combining the results into a structured response

## Components

### Database Layer
- SQLite database containing:
  - `applicants` table: Basic personal information
  - `financial_data` table: Income, credit scores, loan amounts
  - `loan_history` table: Previous applications and repayment history

### ML Service Layer
- Mock HTTP server simulating a loan approval model
- Processes applicant features and returns:
  - Approval probability
  - Decision (Approved/Denied)
  - Risk tier classification
  - Interest rate recommendation
  - Key decision factors with weights

### Orchestration Layer
- Configures data flow between components
- Maps database fields to ML model features
- Formats structured responses for clients

## Running the Example

### Option 1: Quick Demo with Complete Example

For a simple demonstration without setting up separate services:

```bash
python examples/loan_prediction/run_complete_example.py --setup-db
```

This will:
1. Set up the database
2. Run the entire prediction flow in-process
3. Display the formatted results

Try with different applicants:
```bash
python examples/loan_prediction/run_complete_example.py --applicant app_1002
```

### Option 2: Running with Separate Services

For a more realistic setup with actual service components:

1. First, set up the database:
   ```bash
   python examples/loan_prediction/setup_database.py
   ```

2. Start the mock ML service (on port 5001):
   ```bash
   python examples/loan_prediction/simple_ml_server.py 5001
   ```

3. In a new terminal, start the orchestrator API service with the loan prediction example enabled:
   ```bash
   python main.py --with-loan-prediction
   ```
   
   This flag:
   - Loads the loan prediction example controllers and routes
   - Sets up the correct configurations from examples/loan_prediction/config
   - Configures the database and ML model clients

4. In a new terminal, run the client to test:
   ```bash
   python examples/loan_prediction/get_loan_prediction.py app_1001
   ```

## Test Applicants

The example database includes several test profiles:

| ID | Name | Credit | Income | DTI | History | Expected Outcome |
|----|------|--------|--------|-----|---------|-----------------|
| app_1001 | Alex Johnson | 710 | $75,000 | 0.28 | Mixed | Approved (Good) |
| app_1002 | Sarah Williams | 780 | $120,000 | 0.15 | Excellent | Approved (Excellent) |
| app_1003 | Michael Brown | 650 | $60,000 | 0.34 | Average | Approved (Marginal) |
| app_1004 | Emily Davis | 590 | $45,000 | 0.40 | Poor | Denied (High Risk) |
| app_1005 | David Wilson | 520 | $38,000 | 0.52 | Bad | Denied (Very High Risk) |

## How It Works

### Configuration Design

The key configuration files:

- `config/domains/loan_prediction.yaml`: Defines the data flow:
  ```yaml
  endpoints:
    predict:
      data_sources:
        - name: applicant_features
          type: database
          operation: get_applicant_features
          params:
            applicant_id: "$request.applicant_id"
        
        - name: loan_prediction
          type: ml
          operation: predict_loan_approval
          params:
            features: 
              credit_score: "$applicant_features.credit_score"
              annual_income: "$applicant_features.annual_income" 
              # ... more features
  ```

- `config/integrations/ml.yaml`: ML service connection settings:
  ```yaml
  ml:
    sources:
      loan_model:
        base_url: "http://localhost:5001" 
        models:
          loan_approval:
            endpoint: "/"
  ```

### Data Flow Sequence

1. Client sends request with `applicant_id`
2. Orchestrator retrieves applicant data from database
3. Orchestrator transforms data into ML model input format
4. ML service makes prediction based on applicant features
5. Orchestrator combines database data with ML predictions
6. Client receives unified response with loan decision

## Example Response

```json
{
  "applicant_id": "app_1001",
  "loan_details": {
    "amount": 250000.00,
    "term": 30,
    "purpose": "Home Purchase"
  },
  "financial_summary": {
    "annual_income": 75000.00,
    "credit_score": 710,
    "debt_to_income": 0.28,
    "employment_years": 8
  },
  "prediction": {
    "approval_probability": 0.82,
    "decision": "Approved",
    "risk_tier": "Low Risk",
    "suggested_interest_rate": 4.75
  },
  "key_factors": {
    "credit_score": {
      "value": 710,
      "impact": 0.85,
      "weight": 0.40
    },
    "debt_to_income": {
      "value": 0.28,
      "impact": 0.75,
      "weight": 0.30
    },
    "income_vs_loan": {
      "value": "$75,000.00 / $250,000.00",
      "impact": 0.78,
      "weight": 0.20
    },
    "employment_history": {
      "value": "8 years",
      "impact": 0.90,
      "weight": 0.10
    }
  }
}
```

## Extending This Example

You can build upon this example in several ways:

1. **Add feature engineering**
   - Implement credit score normalization
   - Calculate affordability metrics
   - Add fraud detection features

2. **Enhance the ML model**
   - Implement multiple models for different loan types
   - Add model versioning support
   - Implement A/B testing capabilities

3. **Add additional data sources**
   - Credit bureau API integration
   - External fraud detection service
   - Employment verification service

4. **Build a front-end**
   - React/Vue application for loan officers
   - Mobile app for applicants
   - Admin dashboard for model performance

## Files in This Example

- `setup_database.py`: Creates and populates the SQLite database
- `mock_ml_service.py`: HTTP server simulating the ML prediction service
- `simple_ml_server.py`: Simplified version for easier testing
- `get_loan_prediction.py`: Client script to query the API
- `run_example.py`: Script that runs the services in sequence
- `run_complete_example.py`: End-to-end example that runs in a single process
- `test_services.py`: Testing utility for the individual components