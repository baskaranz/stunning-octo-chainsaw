#!/usr/bin/env python3
"""
Generic Orchestrator Example - API Client

This script demonstrates how to call the generic orchestrator API
for the different model endpoints.
"""

import argparse
import json
import requests
import sys
from typing import Dict, Any, Optional

def call_credit_risk_api(
    customer_id: Optional[str] = None,
    features: Optional[Dict[str, Any]] = None,
    host: str = "localhost",
    port: int = 8000
) -> Dict[str, Any]:
    """
    Call the credit risk scoring API.
    
    Args:
        customer_id: Optional customer ID for database lookup
        features: Optional features for direct scoring
        host: API host
        port: API port
        
    Returns:
        The credit risk assessment result
    """
    base_url = f"http://{host}:{port}/orchestrator/model_scoring/credit_risk"
    
    # Build URL with customer ID if provided
    if customer_id:
        url = f"{base_url}/{customer_id}"
        
        # If also passing features, use POST
        if features:
            try:
                response = requests.post(url, json=features)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error calling API: {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"Response: {e.response.text}")
                sys.exit(1)
        else:
            # Just customer ID, use GET
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error calling API: {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"Response: {e.response.text}")
                sys.exit(1)
    elif features:
        # Only features, use POST to base URL
        try:
            response = requests.post(base_url, json=features)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling API: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            sys.exit(1)
    else:
        print("Error: Either customer_id or features must be provided")
        sys.exit(1)

def call_product_recommender_api(
    customer_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    host: str = "localhost",
    port: int = 8000
) -> Dict[str, Any]:
    """
    Call the product recommender API.
    
    Args:
        customer_id: Optional customer ID for database lookup
        context: Optional context information like current page
        host: API host
        port: API port
        
    Returns:
        The product recommendations
    """
    base_url = f"http://{host}:{port}/orchestrator/model_scoring/product_recommender"
    
    # Build URL with customer ID if provided
    if customer_id:
        url = f"{base_url}/{customer_id}"
        
        # If also passing context, use POST
        if context:
            try:
                response = requests.post(url, json=context)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error calling API: {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"Response: {e.response.text}")
                sys.exit(1)
        else:
            # Just customer ID, use GET
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error calling API: {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"Response: {e.response.text}")
                sys.exit(1)
    elif context:
        # Only context, use POST to base URL
        try:
            response = requests.post(base_url, json=context)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling API: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            sys.exit(1)
    else:
        print("Error: Either customer_id or context must be provided")
        sys.exit(1)

def print_credit_risk(result: Dict[str, Any]) -> None:
    """Pretty print the credit risk result."""
    print("\n" + "=" * 70)
    print(f"CREDIT RISK ASSESSMENT FOR: {result.get('name', 'Unknown')} ({result.get('customer_id', 'Unknown')})")
    print("=" * 70)
    
    # Risk score info
    risk_score = result.get('risk_score', {})
    score = risk_score.get('score', 0)
    risk_tier = risk_score.get('risk_tier', 'Unknown')
    probability = risk_score.get('default_probability', 0)
    confidence = risk_score.get('confidence', 0)
    
    # Color based on risk tier
    if risk_tier == "Low":
        color = "\033[92m"  # Green
    elif risk_tier == "Medium":
        color = "\033[93m"  # Yellow
    elif risk_tier == "High":
        color = "\033[91m"  # Red
    elif risk_tier == "Very High":
        color = "\033[91m\033[1m"  # Bold Red
    else:
        color = ""
    
    reset = "\033[0m"
    
    print(f"\nRISK ASSESSMENT:")
    print(f"  Score: {score}/100")
    print(f"  Risk Tier: {color}{risk_tier}{reset}")
    print(f"  Default Probability: {probability:.2%}")
    print(f"  Confidence: {confidence:.2%}")
    
    # Credit profile
    credit_profile = result.get('credit_profile', {})
    if credit_profile:
        print("\nCREDIT PROFILE:")
        print(f"  Credit Score: {credit_profile.get('credit_score', 'N/A')}")
        
        dti = credit_profile.get('debt_to_income')
        if dti is not None:
            print(f"  Debt-to-Income Ratio: {dti:.2%}")
        else:
            print("  Debt-to-Income Ratio: N/A")
        
        payment_history = credit_profile.get('payment_history_score')
        if payment_history is not None:
            print(f"  Payment History Score: {payment_history:.2%}")
        else:
            print("  Payment History Score: N/A")
    
    # Key factors
    key_factors = result.get('key_factors', [])
    if key_factors:
        print("\nKEY FACTORS:")
        for factor in key_factors:
            impact = factor.get('impact', 0)
            description = factor.get('description', 'Unknown factor')
            
            if impact >= 0:
                impact_str = f"+{impact:.2%}"
                factor_color = "\033[92m"  # Green
            else:
                impact_str = f"{impact:.2%}"
                factor_color = "\033[91m"  # Red
            
            print(f"  • {description}: {factor_color}{impact_str}{reset}")
    
    # Recommended actions
    actions = result.get('recommended_actions', [])
    if actions:
        print("\nRECOMMENDED ACTIONS:")
        for i, action in enumerate(actions, 1):
            description = action.get('description', action.get('action', 'Unknown action'))
            confidence = action.get('confidence', 0)
            print(f"  {i}. {description} (Confidence: {confidence:.2%})")
    
    print("\n" + "=" * 70)

def print_product_recommendations(result: Dict[str, Any]) -> None:
    """Pretty print the product recommendations."""
    print("\n" + "=" * 70)
    print(f"PRODUCT RECOMMENDATIONS FOR: {result.get('customer_id', 'Unknown')}")
    print("=" * 70)
    
    # Context information
    context = result.get('context', {})
    current_page = context.get('current_page', 'N/A')
    based_on = context.get('based_on', [])
    
    if current_page:
        print(f"\nCurrent category: {current_page}")
    
    if based_on:
        print(f"Recommendations based on: {', '.join(based_on)}")
    
    # Print recommendations
    recommendations = result.get('recommendations', [])
    if recommendations:
        print("\nRECOMMENDED PRODUCTS:")
        for i, product in enumerate(recommendations, 1):
            name = product.get('name', 'Unknown Product')
            product_id = product.get('product_id', 'unknown')
            score = product.get('relevance_score', 0)
            price_tier = product.get('price_tier', 'unknown')
            category = product.get('category', 'unknown')
            
            # Color for price tier
            if price_tier == "budget":
                tier_color = "\033[92m"  # Green
            elif price_tier == "mid-range":
                tier_color = "\033[93m"  # Yellow
            elif price_tier == "premium":
                tier_color = "\033[94m"  # Blue
            elif price_tier == "luxury":
                tier_color = "\033[95m"  # Purple
            else:
                tier_color = ""
            
            reset = "\033[0m"
            
            print(f"  {i}. {name} ({product_id})")
            print(f"     Category: {category}")
            print(f"     Price Tier: {tier_color}{price_tier}{reset}")
            print(f"     Relevance: {score:.2%}")
            print()
    else:
        print("\nNo recommendations found.")
    
    print("=" * 70)

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
        
        # Handle pipe-separated lists
        if '|' in value:
            value = value.split('|')
            
        # Try to convert to appropriate types
        elif value.lower() == 'true':
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
    """Main function to parse arguments and call the APIs."""
    parser = argparse.ArgumentParser(description="Call the generic orchestrator APIs")
    parser.add_argument("model", choices=["credit-risk", "product-recommender"], 
                       help="Model endpoint to call")
    parser.add_argument("--id", help="Customer ID")
    parser.add_argument("--features", help="Features in key=value format (e.g., credit_score=700,income=50000)")
    parser.add_argument("--context", help="Context in key=value format (e.g., current_page=electronics)")
    parser.add_argument("--host", default="localhost", help="API host (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    
    args = parser.parse_args()
    
    # Parse arguments
    features_dict = parse_key_value_arg(args.features) if args.features else None
    context_dict = parse_key_value_arg(args.context) if args.context else None
    
    # Call the appropriate API
    if args.model == "credit-risk":
        result = call_credit_risk_api(
            customer_id=args.id,
            features=features_dict,
            host=args.host,
            port=args.port
        )
        
        # Print the result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_credit_risk(result)
    
    elif args.model == "product-recommender":
        result = call_product_recommender_api(
            customer_id=args.id,
            context=context_dict,
            host=args.host,
            port=args.port
        )
        
        # Print the result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_product_recommendations(result)

if __name__ == "__main__":
    main()