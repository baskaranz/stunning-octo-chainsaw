#!/usr/bin/env python3
"""
Customer 360 Mock Services

This script provides mock implementations of the various services required
for the Customer 360 example. It simulates:
- Database for customer profiles and orders
- Feature store for customer behavior metrics
- External API for credit scores
- ML service for churn predictions

Run this before testing the Customer 360 API.
"""

import argparse
import json
import random
import time
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List
import uuid
import re

# Sample data
CUSTOMERS = {
    "cust_12345": {
        "customer_id": "cust_12345",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "address": "123 Main St, San Francisco, CA 94105",
        "date_of_birth": "1990-01-01",
        "created_at": "2022-03-15T10:30:00Z",
        "updated_at": "2023-04-20T15:45:00Z"
    },
    "cust_67890": {
        "customer_id": "cust_67890",
        "name": "Jane Smith", 
        "email": "jane.smith@example.com",
        "phone": "+0987654321",
        "address": "456 Oak St, New York, NY 10001",
        "date_of_birth": "1985-05-15",
        "created_at": "2020-08-10T14:20:00Z",
        "updated_at": "2023-02-28T09:15:00Z"
    },
    "cust_24680": {
        "customer_id": "cust_24680",
        "name": "Michael Johnson",
        "email": "michael.johnson@example.com",
        "phone": "+1122334455",
        "address": "789 Pine St, Seattle, WA 98101",
        "date_of_birth": "1978-11-30",
        "created_at": "2021-05-22T11:00:00Z",
        "updated_at": "2022-12-15T16:30:00Z"
    }
}

# Mock orders data
ORDERS = {
    "cust_12345": [
        {
            "order_id": "ord_98765",
            "order_date": "2023-03-15T14:30:00Z",
            "total_amount": 95.50,
            "status": "Delivered",
            "items_count": 3
        },
        {
            "order_id": "ord_87654",
            "order_date": "2023-02-22T10:15:00Z",
            "total_amount": 120.75,
            "status": "Delivered",
            "items_count": 4
        },
        {
            "order_id": "ord_76543",
            "order_date": "2023-01-10T16:45:00Z",
            "total_amount": 75.20,
            "status": "Delivered",
            "items_count": 2
        }
    ],
    "cust_67890": [
        {
            "order_id": "ord_54321",
            "order_date": "2023-04-05T09:30:00Z",
            "total_amount": 150.00,
            "status": "Processing",
            "items_count": 5
        },
        {
            "order_id": "ord_43210",
            "order_date": "2023-03-20T13:45:00Z",
            "total_amount": 85.99,
            "status": "Delivered",
            "items_count": 3
        }
    ],
    "cust_24680": [
        {
            "order_id": "ord_32109",
            "order_date": "2023-04-10T11:20:00Z",
            "total_amount": 220.50,
            "status": "Shipped",
            "items_count": 6
        },
        {
            "order_id": "ord_21098",
            "order_date": "2023-02-28T15:10:00Z",
            "total_amount": 45.25,
            "status": "Delivered",
            "items_count": 1
        },
        {
            "order_id": "ord_10987",
            "order_date": "2023-01-15T12:35:00Z",
            "total_amount": 130.00,
            "status": "Delivered",
            "items_count": 4
        },
        {
            "order_id": "ord_09876",
            "order_date": "2022-12-05T10:50:00Z",
            "total_amount": 95.75,
            "status": "Delivered",
            "items_count": 3
        }
    ]
}

# Mock feature data
FEATURES = {
    "cust_12345": {
        "customer_lifetime_value": 2450.75,
        "days_since_last_purchase": 15,
        "purchase_frequency": 2.3,
        "average_order_value": 85.25,
        "total_purchases": 12
    },
    "cust_67890": {
        "customer_lifetime_value": 3750.50,
        "days_since_last_purchase": 5,
        "purchase_frequency": 3.1,
        "average_order_value": 95.80,
        "total_purchases": 18
    },
    "cust_24680": {
        "customer_lifetime_value": 1850.25,
        "days_since_last_purchase": 10,
        "purchase_frequency": 1.5,
        "average_order_value": 110.25,
        "total_purchases": 8
    }
}

# Mock credit scores
CREDIT_SCORES = {
    "cust_12345": {
        "score": 720,
        "risk_tier": "Low",
        "updated_at": "2023-03-01T00:00:00Z"
    },
    "cust_67890": {
        "score": 680,
        "risk_tier": "Medium",
        "updated_at": "2023-02-15T00:00:00Z"
    },
    "cust_24680": {
        "score": 750,
        "risk_tier": "Low",
        "updated_at": "2023-03-10T00:00:00Z"
    }
}

class MockServiceHandler(BaseHTTPRequestHandler):
    """HTTP request handler for mock services"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Database endpoint - customer profile
        if re.match(r'^/api/v1/database/customers/cust_\d+$', self.path):
            customer_id = self.path.split('/')[-1]
            if customer_id in CUSTOMERS:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(CUSTOMERS[customer_id]).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Customer not found"}).encode())
        
        # Database endpoint - recent orders
        elif re.match(r'^/api/v1/database/customers/cust_\d+/orders$', self.path):
            parts = self.path.split('/')
            customer_id = parts[-2]
            
            if customer_id in ORDERS:
                # Sort orders by date (most recent first)
                sorted_orders = sorted(
                    ORDERS[customer_id], 
                    key=lambda x: x['order_date'], 
                    reverse=True
                )
                
                # Get limit from query string, default to 5
                limit = 5
                if '?' in self.path:
                    query = self.path.split('?')[1]
                    for param in query.split('&'):
                        if param.startswith('limit='):
                            try:
                                limit = int(param.split('=')[1])
                            except ValueError:
                                pass
                
                # Return limited number of orders
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(sorted_orders[:limit]).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Customer not found"}).encode())
        
        # Credit API endpoint
        elif re.match(r'^/api/v1/credit/customers/cust_\d+/credit-score$', self.path):
            customer_id = self.path.split('/')[-2]
            
            if customer_id in CREDIT_SCORES:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(CREDIT_SCORES[customer_id]).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Customer not found"}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        request_data = json.loads(post_data.decode())
        
        # Feature store endpoint
        if self.path == '/api/v1/feast/features':
            customer_id = None
            if 'entity_rows' in request_data and request_data['entity_rows']:
                customer_id = request_data['entity_rows'][0].get('customer_id')
            
            if customer_id and customer_id in FEATURES:
                # Simulate a delay for realism
                time.sleep(0.2)
                
                features = FEATURES[customer_id]
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'customer_id': [customer_id],
                    **{k: [v] for k, v in features.items()}
                }).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Features not found"}).encode())
        
        # ML model endpoint
        elif self.path == '/api/v1/ml/predict/churn':
            features = request_data.get('features', {})
            
            # Generate deterministic but realistic-looking predictions
            if features:
                # Use lifetime value and days since last purchase for a simple prediction
                lifetime_value = features.get('customer_lifetime_value', 0)
                days_since_purchase = features.get('days_since_last_purchase', 0)
                
                # Simple formula to calculate churn probability
                # Lower LTV and higher days since purchase = higher churn probability
                churn_probability = max(0.1, min(0.9, 
                    (0.4 - (lifetime_value / 10000) + (days_since_purchase / 100))
                ))
                
                # Determine risk level
                risk_level = "Low"
                if churn_probability > 0.6:
                    risk_level = "High"
                elif churn_probability > 0.3:
                    risk_level = "Medium"
                
                # Generate a recommendation based on the risk level
                recommendations = {
                    "Low": "Standard Discount Offer",
                    "Medium": "Loyalty Program Upgrade",
                    "High": "Premium Subscription at Special Rate"
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "probability": churn_probability,
                    "risk_level": risk_level,
                    "recommendation": recommendations[risk_level]
                }).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid request data"}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

def main():
    parser = argparse.ArgumentParser(description='Run mock services for Customer 360 example')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()
    
    server = HTTPServer(('localhost', args.port), MockServiceHandler)
    print(f"Starting mock services on http://localhost:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    # Print available endpoints
    print("\nAvailable endpoints:")
    print("  GET /api/v1/database/customers/<customer_id>")
    print("  GET /api/v1/database/customers/<customer_id>/orders?limit=<limit>")
    print("  GET /api/v1/credit/customers/<customer_id>/credit-score")
    print("  POST /api/v1/feast/features")
    print("  POST /api/v1/ml/predict/churn")
    
    print("\nSample customer IDs: cust_12345, cust_67890, cust_24680")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    
    server.server_close()
    print("Server stopped")

if __name__ == "__main__":
    main()