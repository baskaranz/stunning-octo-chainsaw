#!/usr/bin/env python3
"""
Loan Prediction Example - Client Script

This script queries the orchestrator API to get loan approval predictions for an applicant.
"""

import argparse
import json
import requests
import sys
from pathlib import Path

def get_loan_prediction(applicant_id, port=8000):
    """Get loan prediction for the specified applicant."""
    url = f"http://localhost:{port}/api/loan-prediction/predict/{applicant_id}"
    
    try:
        print(f"Requesting loan prediction from: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse and display the prediction results
        result = response.json()
        print(f"Raw response: {json.dumps(result, indent=2)}")
        
        if result is None:
            print("Error: Received None response from the server")
            return False
        
        print("\n===== LOAN PREDICTION RESULTS =====\n")
        
        # Applicant ID and loan details
        print(f"APPLICANT ID: {result.get('applicant_id', 'N/A')}")
        if 'loan_details' in result:
            loan_details = result['loan_details']
            print(f"LOAN DETAILS: ${loan_details.get('amount', 0):,.2f} for {loan_details.get('term', 0)} years ({loan_details.get('purpose', 'N/A')})")
        else:
            print("LOAN DETAILS: Not available")
        
        # Financial summary
        print("\n----- FINANCIAL SUMMARY -----")
        if 'financial_summary' in result:
            fs = result['financial_summary']
            print(f"Annual Income: ${fs.get('annual_income', 0):,.2f}")
            print(f"Credit Score: {fs.get('credit_score', 0)}")
            print(f"Debt-to-Income Ratio: {fs.get('debt_to_income', 0):.2f}")
            print(f"Years Employed: {fs.get('employment_years', 0)}")
        else:
            print("Financial summary not available")
        
        # Prediction results
        print("\n----- PREDICTION RESULTS -----")
        if 'prediction' in result:
            pred = result['prediction']
            print(f"DECISION: {pred.get('decision', 'N/A')}")
            print(f"Approval Probability: {pred.get('approval_probability', 0):.2%}")
            print(f"Risk Tier: {pred.get('risk_tier', 'N/A')}")
            print(f"Suggested Interest Rate: {pred.get('suggested_interest_rate', 0)}%")
        else:
            print("Prediction results not available")
        
        # Key factors
        print("\n----- KEY FACTORS -----")
        if 'key_factors' in result:
            for factor_name, factor in result['key_factors'].items():
                print(f"{factor_name}: {factor.get('value', 'N/A')} (Impact: {factor.get('impact', 0):.2f}, Weight: {factor.get('weight', 0):.2f})")
        else:
            print("Key factors not available")
        
        print("\n===================================\n")
        
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to get prediction results: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Get loan approval prediction for an applicant")
    parser.add_argument(
        "applicant_id", 
        help="Applicant ID to predict (e.g., app_1001)"
    )
    parser.add_argument(
        "--port", "-p", 
        type=int, 
        default=8000,
        help="Port of the orchestrator API service (default: 8000)"
    )
    
    args = parser.parse_args()
    
    success = get_loan_prediction(args.applicant_id, args.port)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()