#!/usr/bin/env python3
"""
Complete Loan Prediction Example - Combines all steps

This script demonstrates the complete loan prediction flow:
1. Setting up the database
2. Running the simplified ML service
3. Making a prediction request through the API
4. Presenting the results
"""

import os
import sys
import time
import json
import argparse
import asyncio
import sqlite3
import subprocess
from pathlib import Path

# Get the absolute path to the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
DB_PATH = PROJECT_ROOT / "examples" / "loan_prediction" / "loan_prediction.db"

def setup_database():
    """Set up the SQLite database for the Loan Prediction example."""
    print("\n=== Setting up the database ===")
    setup_script = PROJECT_ROOT / "examples" / "loan_prediction" / "setup_database.py"
    
    try:
        subprocess.run([sys.executable, str(setup_script)], check=True)
        print("Database setup successful.")
        return True
    except subprocess.CalledProcessError:
        print("Database setup failed.")
        return False

async def get_applicant_features(applicant_id="app_1001"):
    """Get applicant features from the database."""
    print(f"\n=== Retrieving features for applicant {applicant_id} ===")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Execute the SQL query to get applicant features
        cursor.execute("""
        SELECT 
          a.applicant_id,
          a.age,
          f.annual_income,
          f.credit_score,
          f.debt_to_income,
          f.employment_years,
          f.loan_amount,
          f.loan_term,
          f.loan_purpose,
          h.previous_applications,
          h.approved_loans,
          h.rejected_loans,
          h.current_loans,
          h.total_current_debt,
          CASE WHEN h.previous_applications > 0 
               THEN CAST(h.approved_loans AS FLOAT) / h.previous_applications 
               ELSE 0 
          END AS approval_ratio
        FROM 
          applicants a
          JOIN financial_data f ON a.applicant_id = f.applicant_id
          JOIN loan_history h ON a.applicant_id = h.applicant_id
        WHERE 
          a.applicant_id = ?
        """, (applicant_id,))
        
        # Get column names and result row
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        
        if row:
            # Convert to dictionary
            features = dict(zip(columns, row))
            print(f"Features retrieved for applicant {applicant_id}")
            return features
        else:
            print(f"Applicant {applicant_id} not found")
            return None
    except Exception as e:
        print(f"Error retrieving applicant features: {str(e)}")
        return None
    finally:
        conn.close()

async def make_prediction(features):
    """Make a prediction using the ML service."""
    if not features:
        print("Cannot make prediction without features")
        return None
    
    print("\n=== Making prediction using features ===")
    
    # Prepare the request data for the ML service
    request_data = {
        "features": {k: v for k, v in features.items() if k != "loan_purpose"}
    }
    
    # This function would normally use the ML service, but for simplicity
    # we'll just return a hardcoded prediction
    print("Using hardcoded prediction since this is a complete example")
    
    prediction = {
        "probability": 0.82,
        "decision": "Approved",
        "risk_tier": "Low Risk",
        "suggested_interest_rate": 4.75,
        "factors": {
            "credit_score": {
                "value": features.get("credit_score", 0),
                "impact": 0.85,
                "weight": 0.4
            },
            "debt_to_income": {
                "value": features.get("debt_to_income", 0),
                "impact": 0.75,
                "weight": 0.3
            },
            "income_vs_loan": {
                "value": f"${features.get('annual_income', 0):,.2f} / ${features.get('loan_amount', 0):,.2f}",
                "impact": 0.78,
                "weight": 0.2
            },
            "employment_history": {
                "value": f"{features.get('employment_years', 0)} years",
                "impact": 0.9,
                "weight": 0.1
            }
        }
    }
    
    return prediction

async def format_response(features, prediction):
    """Format the response according to the API specification."""
    if not features or not prediction:
        print("Cannot format response without features and prediction")
        return None
    
    print("\n=== Formatting response ===")
    
    # Map the data to the expected response format
    response = {
        "applicant_id": features.get("applicant_id"),
        "loan_details": {
            "amount": features.get("loan_amount"),
            "term": features.get("loan_term"),
            "purpose": features.get("loan_purpose")
        },
        "financial_summary": {
            "annual_income": features.get("annual_income"),
            "credit_score": features.get("credit_score"),
            "debt_to_income": features.get("debt_to_income"),
            "employment_years": features.get("employment_years")
        },
        "prediction": {
            "approval_probability": prediction.get("probability"),
            "decision": prediction.get("decision"),
            "risk_tier": prediction.get("risk_tier"),
            "suggested_interest_rate": prediction.get("suggested_interest_rate")
        },
        "key_factors": prediction.get("factors", {})
    }
    
    return response

def display_results(response):
    """Display the loan prediction results in a user-friendly format."""
    if not response:
        print("No results to display")
        return
    
    print("\n===== LOAN PREDICTION RESULTS =====\n")
    
    # Applicant ID and loan details
    print(f"APPLICANT ID: {response.get('applicant_id', 'N/A')}")
    if 'loan_details' in response:
        loan_details = response['loan_details']
        print(f"LOAN DETAILS: ${loan_details.get('amount', 0):,.2f} for {loan_details.get('term', 0)} years ({loan_details.get('purpose', 'N/A')})")
    else:
        print("LOAN DETAILS: Not available")
    
    # Financial summary
    print("\n----- FINANCIAL SUMMARY -----")
    if 'financial_summary' in response:
        fs = response['financial_summary']
        print(f"Annual Income: ${fs.get('annual_income', 0):,.2f}")
        print(f"Credit Score: {fs.get('credit_score', 0)}")
        print(f"Debt-to-Income Ratio: {fs.get('debt_to_income', 0):.2f}")
        print(f"Years Employed: {fs.get('employment_years', 0)}")
    else:
        print("Financial summary not available")
    
    # Prediction results
    print("\n----- PREDICTION RESULTS -----")
    if 'prediction' in response:
        pred = response['prediction']
        print(f"DECISION: {pred.get('decision', 'N/A')}")
        print(f"Approval Probability: {pred.get('approval_probability', 0):.2%}")
        print(f"Risk Tier: {pred.get('risk_tier', 'N/A')}")
        print(f"Suggested Interest Rate: {pred.get('suggested_interest_rate', 0)}%")
    else:
        print("Prediction results not available")
    
    # Key factors
    print("\n----- KEY FACTORS -----")
    if 'key_factors' in response:
        for factor_name, factor in response['key_factors'].items():
            print(f"{factor_name}: {factor.get('value', 'N/A')} (Impact: {factor.get('impact', 0):.2f}, Weight: {factor.get('weight', 0):.2f})")
    else:
        print("Key factors not available")
    
    print("\n===================================\n")

async def run_loan_prediction(applicant_id="app_1001"):
    """Run the loan prediction workflow end-to-end."""
    print(f"\n=== Running Loan Prediction for applicant {applicant_id} ===")
    
    # Get applicant features from database
    features = await get_applicant_features(applicant_id)
    if not features:
        print(f"Couldn't retrieve features for applicant {applicant_id}")
        return False
    
    # Make prediction using ML service
    prediction = await make_prediction(features)
    if not prediction:
        print("Couldn't make prediction")
        return False
    
    # Format response
    response = await format_response(features, prediction)
    if not response:
        print("Couldn't format response")
        return False
    
    # Display results
    display_results(response)
    return True

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Run the complete loan prediction example")
    parser.add_argument(
        "--applicant", "-a", 
        default="app_1001",
        help="Applicant ID to use for the prediction (default: app_1001)"
    )
    parser.add_argument(
        "--setup-db",
        action="store_true",
        help="Setup the database before running the example"
    )
    
    args = parser.parse_args()
    
    # Setup database if requested
    if args.setup_db:
        if not setup_database():
            print("Exiting due to database setup failure")
            sys.exit(1)
    
    # Run the loan prediction workflow
    asyncio.run(run_loan_prediction(args.applicant))

if __name__ == "__main__":
    main()