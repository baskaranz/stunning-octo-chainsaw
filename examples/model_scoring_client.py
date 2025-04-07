#!/usr/bin/env python3
"""
Model Scoring Client

This script provides a command-line interface for testing the model scoring endpoints
of the orchestrator API. It allows scoring with different models using either GET or POST
requests with various input options.
"""

import argparse
import json
import requests
import sys
from typing import Dict, Any, Optional

def score_model(
    model_name: str,
    entity_id: Optional[str] = None,
    features: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, Any]] = None,
    host: str = "localhost",
    port: int = 8000
) -> Dict[str, Any]:
    """
    Score a model through the orchestrator API.
    
    Args:
        model_name: The name of the model (e.g., 'churn_pred', 'loan_pred')
        entity_id: Optional entity ID (customer_id, applicant_id) to look up in database
        features: Optional dictionary of feature values for direct scoring
        query_params: Optional query parameters
        host: API host
        port: API port
        
    Returns:
        The API response with prediction results
    """
    base_url = f"http://{host}:{port}/orchestrator/model_scoring/{model_name}"
    query_params = query_params or {}
    
    # Determine if we should use POST or GET based on presence of features
    if features and entity_id:
        # POST with both entity ID and features
        url = f"{base_url}/{entity_id}"
        try:
            response = requests.post(url, json=features, params=query_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            sys.exit(1)
    elif features:
        # POST with just features for direct scoring
        try:
            response = requests.post(base_url, json=features, params=query_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            sys.exit(1)
    elif entity_id:
        # GET with entity ID for database lookup
        url = f"{base_url}/{entity_id}"
        try:
            response = requests.get(url, params=query_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            sys.exit(1)
    else:
        print("Error: Either entity_id or features must be provided")
        sys.exit(1)

def print_prediction(prediction: Dict[str, Any], model_name: str) -> None:
    """
    Print the prediction result in a friendly format.
    
    Args:
        prediction: The prediction result from the API
        model_name: The name of the model used
    """
    # Different printing formats based on model type
    print("\n" + "=" * 60)
    
    if model_name == "churn_pred":
        # Customer churn prediction format
        print(f"CHURN PREDICTION FOR: {prediction.get('company_name', 'Unknown')} ({prediction.get('customer_id', 'Unknown')})")
        print("=" * 60)
        
        # Get the prediction values
        churn_pred = prediction.get('churn_prediction', {})
        risk_tier = churn_pred.get('risk_tier', 'Unknown')
        probability = churn_pred.get('probability', 0)
        
        # Color code based on risk tier
        if risk_tier == "Low":
            risk_color = "\033[92m"  # Green
        elif risk_tier == "Medium":
            risk_color = "\033[93m"  # Yellow
        elif risk_tier == "High":
            risk_color = "\033[91m"  # Red
        elif risk_tier == "Critical":
            risk_color = "\033[91m\033[1m"  # Bold Red
        else:
            risk_color = ""
        
        reset_color = "\033[0m"
        
        print(f"\nRISK ASSESSMENT: {risk_color}{risk_tier} Risk{reset_color} ({probability * 100:.1f}% probability)")
        print(f"Confidence: {churn_pred.get('confidence', 0) * 100:.1f}%")
        print(f"Date: {prediction.get('prediction_date', 'Unknown')}")
        
        # Print subscription info
        subscription = prediction.get('subscription', {})
        print("\nSUBSCRIPTION:")
        print(f"  Plan: {subscription.get('plan', 'Unknown')}")
        print(f"  Monthly Amount: ${subscription.get('monthly_amount', 0):.2f}")
        print(f"  Renewal Date: {subscription.get('renewal_date', 'Unknown')}")
        
        # Print key factors
        key_factors = prediction.get('key_factors', {})
        print("\nKEY FACTORS:")
        
        # Positive factors
        if 'positive' in key_factors and key_factors['positive']:
            print("  Positive Factors:")
            for factor in key_factors['positive']:
                impact = int(factor.get('impact', 0) * 100)
                print(f"  + {factor.get('description', 'Unknown')} (+{impact}%)")
        
        # Negative factors
        if 'negative' in key_factors and key_factors['negative']:
            print("\n  Negative Factors:")
            for factor in key_factors['negative']:
                impact = int(abs(factor.get('impact', 0)) * 100)
                print(f"  - {factor.get('description', 'Unknown')} (-{impact}%)")
        
        # Print recommended actions
        actions = prediction.get('recommended_actions', [])
        if actions:
            print("\nRECOMMENDED ACTIONS:")
            for i, action in enumerate(actions, 1):
                priority = action.get('priority', 'Medium')
                if priority == "High":
                    priority_color = "\033[91m"  # Red
                elif priority == "Medium":
                    priority_color = "\033[93m"  # Yellow
                else:
                    priority_color = "\033[92m"  # Green
                    
                impact = int(action.get('expected_impact', 0) * 100)
                print(f"  {i}. {action.get('action', 'Unknown')}")
                print(f"     Impact: +{impact}% | Priority: {priority_color}{priority}{reset_color}")
    
    elif model_name == "loan_pred":
        # Loan prediction format
        print(f"LOAN PREDICTION FOR APPLICANT: {prediction.get('applicant_id', 'Unknown')}")
        print("=" * 60)
        
        # Print loan details
        loan_details = prediction.get('loan_details', {})
        print("\nLOAN DETAILS:")
        print(f"  Amount: ${loan_details.get('amount', 0):,.2f}")
        print(f"  Term: {loan_details.get('term', 0)} months")
        print(f"  Purpose: {loan_details.get('purpose', 'Unknown')}")
        
        # Get the prediction values
        pred = prediction.get('prediction', {})
        approval_prob = pred.get('approval_probability', 0)
        decision = pred.get('decision', 'Unknown')
        risk_tier = pred.get('risk_tier', 'Unknown')
        
        # Color code based on decision
        if decision.lower() == "approve":
            decision_color = "\033[92m"  # Green
        else:
            decision_color = "\033[91m"  # Red
        
        reset_color = "\033[0m"
        
        print("\nPREDICTION RESULT:")
        print(f"  Decision: {decision_color}{decision}{reset_color}")
        print(f"  Approval Probability: {approval_prob * 100:.1f}%")
        print(f"  Risk Tier: {risk_tier}")
        print(f"  Suggested Interest Rate: {pred.get('suggested_interest_rate', 0):.2f}%")
        
        # Print key factors
        factors = prediction.get('key_factors', [])
        if factors:
            print("\nKEY FACTORS:")
            for factor in factors:
                impact = factor.get('impact', 0)
                if impact > 0:
                    impact_str = f"+{impact * 100:.1f}%"
                    impact_color = "\033[92m"  # Green
                else:
                    impact_str = f"{impact * 100:.1f}%"
                    impact_color = "\033[91m"  # Red
                
                print(f"  • {factor.get('factor', 'Unknown')}: {impact_color}{impact_str}{reset_color}")
    
    else:
        # Generic format for other model types
        print(f"PREDICTION RESULT FOR MODEL: {model_name}")
        print("=" * 60)
        print(json.dumps(prediction, indent=2))
    
    print("\n" + "=" * 60 + "\n")

def parse_key_value_arg(arg_str: str) -> Dict[str, Any]:
    """
    Parse a key=value argument into a dictionary.
    
    Args:
        arg_str: String in the format "key1=value1,key2=value2"
        
    Returns:
        Dictionary of parsed key-value pairs
    """
    if not arg_str:
        return {}
    
    result = {}
    pairs = arg_str.split(',')
    
    for pair in pairs:
        if '=' not in pair:
            print(f"Warning: Skipping invalid key-value pair '{pair}' (missing '=')")
            continue
        
        key, value = pair.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Try to convert to appropriate types
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '', 1).isdigit() and value.count('.') <= 1:
            value = float(value)
        
        result[key] = value
    
    return result

def main():
    """Parse command line arguments and call the API"""
    parser = argparse.ArgumentParser(description='Model Scoring Client for Orchestrator API')
    parser.add_argument('model', help='Model name (e.g., churn_pred, loan_pred)')
    parser.add_argument('--id', help='Entity ID (customer_id, applicant_id) for database lookup')
    parser.add_argument('--features', help='Feature values in key=value format (e.g., age=30,income=50000)')
    parser.add_argument('--params', help='Query parameters in key=value format (e.g., tickets=3,nps=7)')
    parser.add_argument('--host', default='localhost', help='API host (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='API port (default: 8000)')
    parser.add_argument('--json', action='store_true', help='Output raw JSON instead of formatted text')
    
    args = parser.parse_args()
    
    # Parse features and params
    features = parse_key_value_arg(args.features) if args.features else None
    params = parse_key_value_arg(args.params) if args.params else None
    
    # Call the API
    result = score_model(
        model_name=args.model,
        entity_id=args.id,
        features=features,
        query_params=params,
        host=args.host,
        port=args.port
    )
    
    # Print the result
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_prediction(result, args.model)

if __name__ == "__main__":
    main()