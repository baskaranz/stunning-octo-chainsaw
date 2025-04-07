#!/usr/bin/env python3
"""
Modified run script to start services and manually test them
"""

import os
import sys
import time
import requests
from pathlib import Path

# Get the absolute path to the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()

def setup_database():
    """Set up the SQLite database for the Loan Prediction example."""
    print("\n=== Setting up the database ===")
    setup_script = PROJECT_ROOT / "examples" / "loan_prediction" / "setup_database.py"
    
    # Run the setup script using the system Python interpreter
    os.system(f"{sys.executable} {setup_script}")
    print("Database setup complete.")

def run_example():
    """Run the loan prediction example manually."""
    print("\n=== Testing the orchestration flow ===")
    
    # Step 1: Get applicant features from database
    print("\nStep 1: Retrieving applicant features from database")
    db_path = PROJECT_ROOT / "examples" / "loan_prediction" / "loan_prediction.db"
    
    # Use the database client from the orchestrator-api-service to get applicant features
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
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
        """, ('app_1001',))
        
        # Get column names and result row
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        
        if row:
            # Convert to dictionary
            applicant_features = dict(zip(columns, row))
            print("Applicant features retrieved:")
            for key, value in applicant_features.items():
                print(f"  {key}: {value}")
        else:
            print("Applicant not found!")
            applicant_features = {}
        
        conn.close()
    except Exception as e:
        print(f"Error retrieving applicant features: {str(e)}")
        applicant_features = {}
    
    # Step 2: Send features to ML service for prediction
    print("\nStep 2: Sending features to ML service for prediction")
    
    if applicant_features:
        try:
            # Prepare request data
            request_data = {
                "features": {
                    "applicant_id": applicant_features["applicant_id"],
                    "age": applicant_features["age"],
                    "annual_income": applicant_features["annual_income"],
                    "credit_score": applicant_features["credit_score"],
                    "debt_to_income": applicant_features["debt_to_income"],
                    "employment_years": applicant_features["employment_years"],
                    "loan_amount": applicant_features["loan_amount"],
                    "loan_term": applicant_features["loan_term"],
                    "current_loans": applicant_features["current_loans"],
                    "total_current_debt": applicant_features["total_current_debt"],
                    "approval_ratio": applicant_features["approval_ratio"]
                }
            }
            
            print(f"Request data: {request_data}")
            
            # Make request to ML service
            print("\nSending request directly to mock ML service (port 5001):")
            response = requests.post("http://localhost:5001", json=request_data)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                prediction = response.json()
                print(f"Prediction result: {prediction}")
                
                # Step 3: Map response to the expected format
                print("\nStep 3: Mapping response to expected format")
                
                mapped_response = {
                    "applicant_id": applicant_features["applicant_id"],
                    "loan_details": {
                        "amount": applicant_features["loan_amount"],
                        "term": applicant_features["loan_term"],
                        "purpose": applicant_features["loan_purpose"]
                    },
                    "financial_summary": {
                        "annual_income": applicant_features["annual_income"],
                        "credit_score": applicant_features["credit_score"],
                        "debt_to_income": applicant_features["debt_to_income"],
                        "employment_years": applicant_features["employment_years"]
                    },
                    "prediction": {
                        "approval_probability": prediction.get("probability", 0),
                        "decision": prediction.get("decision", "Unknown"),
                        "risk_tier": prediction.get("risk_tier", "Unknown"),
                        "suggested_interest_rate": prediction.get("suggested_interest_rate", 0)
                    },
                    "key_factors": prediction.get("factors", {})
                }
                
                print("\nFinal mapped response:")
                import json
                print(json.dumps(mapped_response, indent=2))
                return mapped_response
            else:
                print(f"Error: Failed to get prediction from ML service: {response.text}")
                return None
        except Exception as e:
            print(f"Error making prediction request: {str(e)}")
            return None
    else:
        print("Cannot make prediction without applicant features")
        return None

def main():
    setup_database()
    run_example()
    
if __name__ == "__main__":
    main()