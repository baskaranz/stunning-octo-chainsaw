#!/usr/bin/env python3
"""
Test script for Loan Prediction components
"""

import argparse
import sqlite3
import json
import requests
import sys
from pathlib import Path

def test_database():
    """Test the connection to the loan prediction database."""
    print("\n=== Testing Database Connection ===")
    
    db_path = Path("examples/loan_prediction/loan_prediction.db").absolute()
    print(f"Connecting to database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables found: {', '.join(tables)}")
        
        # Check if there's data in the applicants table
        cursor.execute("SELECT COUNT(*) FROM applicants")
        count = cursor.fetchone()[0]
        print(f"Number of applicants: {count}")
        
        if count > 0:
            # Fetch a sample applicant
            cursor.execute("SELECT * FROM applicants LIMIT 1")
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            applicant = dict(zip(columns, row))
            print(f"Sample applicant: {applicant}")
            
            # Get full data for an applicant
            applicant_id = applicant['applicant_id']
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
            
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            full_data = dict(zip(columns, row))
            
            print("\nFull applicant data:")
            for key, value in full_data.items():
                print(f"  {key}: {value}")
                
            print("\nDatabase test successful!")
            return full_data
        else:
            print("No applicant data found!")
            return None
            
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def test_ml_service(applicant_data=None):
    """Test the ML service connection."""
    print("\n=== Testing ML Service ===")
    
    if not applicant_data:
        # Use some default values
        applicant_data = {
            "applicant_id": "test_001",
            "age": 35,
            "annual_income": 75000,
            "credit_score": 720,
            "debt_to_income": 0.28,
            "employment_years": 5,
            "loan_amount": 250000,
            "loan_term": 30,
            "loan_purpose": "Home Purchase",
            "previous_applications": 2,
            "approved_loans": 1,
            "rejected_loans": 1,
            "current_loans": 1,
            "total_current_debt": 15000,
            "approval_ratio": 0.5
        }
    
    url = "http://localhost:5000/api/v1/ml/predict/loan_approval"
    print(f"Making request to: {url}")
    
    try:
        # Prepare the request data
        request_data = {
            "features": {
                "applicant_id": applicant_data["applicant_id"],
                "age": applicant_data["age"],
                "annual_income": applicant_data["annual_income"],
                "credit_score": applicant_data["credit_score"],
                "debt_to_income": applicant_data["debt_to_income"],
                "employment_years": applicant_data["employment_years"],
                "loan_amount": applicant_data["loan_amount"],
                "loan_term": applicant_data["loan_term"],
                "current_loans": applicant_data["current_loans"],
                "total_current_debt": applicant_data["total_current_debt"],
                "approval_ratio": applicant_data["approval_ratio"]
            }
        }
        
        print(f"Request data: {json.dumps(request_data, indent=2)}")
        
        # Make the request
        response = requests.post(url, json=request_data)
        response.raise_for_status()
        
        # Parse and display the prediction results
        result = response.json()
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response data: {json.dumps(result, indent=2)}")
        
        print("\nML service test successful!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to ML service: {str(e)}")
        return False
    
def main():
    parser = argparse.ArgumentParser(description="Test Loan Prediction components")
    parser.add_argument("--skip-db", action="store_true", help="Skip database test")
    parser.add_argument("--skip-ml", action="store_true", help="Skip ML service test")
    
    args = parser.parse_args()
    
    applicant_data = None
    
    if not args.skip_db:
        applicant_data = test_database()
    
    if not args.skip_ml:
        test_ml_service(applicant_data)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()