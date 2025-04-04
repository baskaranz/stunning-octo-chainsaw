#!/usr/bin/env python3
"""
Customer 360 Example Client

This script demonstrates how to make requests to the orchestrator API service
to get a comprehensive 360 view of a customer.

Before running this example:
1. Run setup_database.py to create the example database
2. Configure the orchestrator to use the example configuration files with:
   ORCHESTRATOR_CONFIG_PATH=./examples/customer_360/config python -m orchestrator-api-service.main
3. Or copy the example configuration files to the main config directory
"""

import sys
import requests
import json
import os
from datetime import datetime
from pprint import pprint

# Get port from environment or use default 8000
PORT = os.environ.get('ORCHESTRATOR_PORT', '8000')
BASE_URL = f"http://localhost:{PORT}/api"

def format_date(date_str):
    """Format date string for display."""
    try:
        date = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
        return date.strftime("%B %d, %Y")
    except (ValueError, AttributeError):
        return date_str

def format_currency(amount):
    """Format currency amount for display."""
    try:
        return f"${float(amount):.2f}"
    except (ValueError, TypeError):
        return str(amount)

def get_customer_360(customer_id):
    """Get a comprehensive 360-degree view of a customer."""
    print(f"Fetching Customer 360 view for customer {customer_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/customer-360/{customer_id}")
        
        if response.status_code == 404:
            print(f"Error: Customer {customer_id} not found.")
            return
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} {response.reason} for url: {response.url}")
            return
        
        data = response.json()
        
        # Display the customer 360 data in a readable format
        print("\n=== Customer 360 View ===\n")
        
        # Basic information
        print(f"Customer ID: {data.get('customer_id')}")
        personal_info = data.get('personal_info', {})
        print(f"Name: {personal_info.get('name')}")
        print(f"Email: {personal_info.get('email')}")
        print(f"Phone: {personal_info.get('phone')}")
        
        # Account information
        account_info = data.get('account_info', {})
        print(f"Account created: {format_date(account_info.get('created_at'))}")
        print(f"Credit score: {account_info.get('credit_score')} (Risk tier: {account_info.get('risk_tier')})")
        
        # Behavior metrics
        print("\n--- Customer Behavior ---")
        behavior = data.get('behavior', {})
        print(f"Lifetime value: {format_currency(behavior.get('lifetime_value'))}")
        print(f"Days since last purchase: {behavior.get('days_since_last_purchase')}")
        print(f"Purchase frequency: {behavior.get('purchase_frequency')} orders per month")
        print(f"Average order value: {format_currency(behavior.get('average_order_value'))}")
        
        # Recent orders
        print("\n--- Recent Orders ---")
        recent_orders = data.get('recent_orders', [])
        for i, order in enumerate(recent_orders, 1):
            print(f"{i}. Order {order.get('order_id')} - {order.get('order_date', '').split('T')[0]} - {format_currency(order.get('total_amount'))} - {order.get('status')}")
        
        # Predictions
        print("\n--- Predictions ---")
        predictions = data.get('predictions', {})
        print(f"Churn probability: {100 * float(predictions.get('churn_probability', 0)):.1f}% ({predictions.get('churn_risk_level')} risk)")
        print(f"Recommended offer: {predictions.get('next_best_offer')}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_customer_360.py <customer_id>")
        print("Example: python get_customer_360.py cust_12345")
        sys.exit(1)
    
    customer_id = sys.argv[1]
    get_customer_360(customer_id)