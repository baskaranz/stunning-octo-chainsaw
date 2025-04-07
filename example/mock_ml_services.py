#!/usr/bin/env python3
"""
Generic Orchestrator Example - Mock ML Services

This script implements mock ML services for the generic orchestrator example.
It simulates the credit risk and product recommendation ML models.
"""

import json
import random
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse

class BaseMockMLHandler(BaseHTTPRequestHandler):
    """Base handler for mock ML services."""
    
    def _set_cors_headers(self):
        """Set CORS headers to allow all origins."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def _send_json_response(self, data, status=200):
        """Send a JSON response with appropriate headers."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_request(self, code='-', size='-'):
        """Override to provide custom logging."""
        print(f"\n=== Request: {self.command} {self.path} ===")
        print(f"From: {self.client_address[0]}:{self.client_address[1]}")
        print(f"Service: {self.__class__.__name__}")

class CreditRiskHandler(BaseMockMLHandler):
    """Handler for credit risk model API."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self._send_json_response({
                "status": "healthy",
                "service": "credit-risk-model",
                "version": "1.0.0"
            })
        else:
            self._send_json_response({
                "message": "Credit Risk Scoring API. Use POST /predict for predictions."
            })
    
    def do_POST(self):
        """Handle POST requests for ML model prediction."""
        if self.path == '/predict':
            # Read request data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                # Parse JSON request
                request_data = json.loads(post_data)
                features = request_data.get('features', {})
                
                # Get customer ID or generate a placeholder
                customer_id = features.get('customer_id', f"unknown_{random.randint(1000, 9999)}")
                
                # Generate credit risk prediction
                prediction = self._generate_credit_risk_prediction(features)
                
                # Send response
                self._send_json_response(prediction)
                
            except json.JSONDecodeError:
                self._send_json_response({"error": "Invalid JSON request"}, 400)
            except Exception as e:
                self._send_json_response({"error": f"Server error: {str(e)}"}, 500)
        else:
            self._send_json_response({"error": "Endpoint not found"}, 404)
    
    def _generate_credit_risk_prediction(self, features):
        """Generate a credit risk prediction based on input features."""
        # Extract features with defaults for missing values
        credit_score = features.get('credit_score', 700)
        debt_to_income = features.get('debt_to_income', 0.3)
        payment_history = features.get('payment_history_score', 0.8)
        missed_payments = features.get('missed_payments_last_year', 0)
        credit_inquiries = features.get('credit_inquiries_last_year', 0)
        
        # Calculate base risk score (higher is better)
        base_score = 0.5
        
        # Adjust for credit score (0-850)
        if credit_score >= 750:
            base_score += 0.3
        elif credit_score >= 700:
            base_score += 0.2
        elif credit_score >= 650:
            base_score += 0.1
        elif credit_score < 600:
            base_score -= 0.2
        
        # Adjust for debt-to-income ratio
        if debt_to_income < 0.2:
            base_score += 0.15
        elif debt_to_income > 0.4:
            base_score -= 0.15
        
        # Adjust for payment history
        base_score += (payment_history - 0.5) * 0.4
        
        # Adjust for missed payments
        base_score -= missed_payments * 0.08
        
        # Adjust for credit inquiries
        base_score -= credit_inquiries * 0.03
        
        # Ensure score is between 0 and 1
        probability = max(0.05, min(0.95, 1 - base_score))
        
        # Convert to a 0-100 score (higher is better)
        score = int((1 - probability) * 100)
        
        # Determine risk tier
        if score >= 80:
            risk_tier = "Low"
        elif score >= 60:
            risk_tier = "Medium"
        elif score >= 40:
            risk_tier = "High"
        else:
            risk_tier = "Very High"
        
        # Generate key factors
        key_factors = self._generate_key_factors(features, score)
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(score, features)
        
        # Create response
        return {
            "customer_id": features.get('customer_id', 'unknown'),
            "prediction_date": datetime.now().isoformat(),
            "risk_score": {
                "score": score,
                "risk_tier": risk_tier,
                "default_probability": round(probability, 2),
                "confidence": round(0.7 + 0.2 * (score / 100), 2)
            },
            "key_factors": key_factors,
            "recommended_actions": recommended_actions
        }
    
    def _generate_key_factors(self, features, score):
        """Generate key factors that influenced the credit risk prediction."""
        factors = []
        
        # Credit score factor
        credit_score = features.get('credit_score', 700)
        if credit_score >= 750:
            factors.append({
                "factor": "excellent_credit_score",
                "description": f"Excellent credit score of {credit_score}",
                "impact": round(0.3, 2)
            })
        elif credit_score < 600:
            factors.append({
                "factor": "poor_credit_score",
                "description": f"Poor credit score of {credit_score}",
                "impact": round(-0.25, 2)
            })
        
        # Payment history factor
        payment_history = features.get('payment_history_score', 0.8)
        if payment_history > 0.9:
            factors.append({
                "factor": "consistent_payment_history",
                "description": "Consistent on-time payment history",
                "impact": round(0.25, 2)
            })
        elif payment_history < 0.7:
            factors.append({
                "factor": "inconsistent_payment_history",
                "description": "Inconsistent payment history",
                "impact": round(-0.2, 2)
            })
        
        # Debt-to-income factor
        debt_to_income = features.get('debt_to_income', 0.3)
        if debt_to_income > 0.4:
            factors.append({
                "factor": "high_debt_to_income",
                "description": f"High debt-to-income ratio of {debt_to_income:.0%}",
                "impact": round(-0.15, 2)
            })
        
        # Missed payments factor
        missed_payments = features.get('missed_payments_last_year', 0)
        if missed_payments > 0:
            factors.append({
                "factor": "recent_missed_payments",
                "description": f"{missed_payments} missed payments in the last year",
                "impact": round(-0.08 * missed_payments, 2)
            })
        
        # Credit inquiries factor
        credit_inquiries = features.get('credit_inquiries_last_year', 0)
        if credit_inquiries > 2:
            factors.append({
                "factor": "multiple_credit_inquiries",
                "description": f"{credit_inquiries} credit inquiries in the last year",
                "impact": round(-0.03 * credit_inquiries, 2)
            })
        
        # Additional random factors for variety
        possible_factors = [
            {
                "factor": "long_customer_relationship",
                "description": "Long-standing customer relationship",
                "impact": round(0.12, 2)
            },
            {
                "factor": "diverse_credit_mix",
                "description": "Diverse mix of credit types",
                "impact": round(0.1, 2)
            },
            {
                "factor": "low_credit_utilization",
                "description": "Low credit utilization ratio",
                "impact": round(0.15, 2)
            },
            {
                "factor": "high_income",
                "description": "Above-average income level",
                "impact": round(0.08, 2)
            },
            {
                "factor": "recent_address_change",
                "description": "Recent change of address",
                "impact": round(-0.05, 2)
            }
        ]
        
        # Add 1-2 random factors
        for _ in range(random.randint(1, 2)):
            if possible_factors:
                factor = random.choice(possible_factors)
                factors.append(factor)
                possible_factors.remove(factor)
        
        return factors
    
    def _generate_recommended_actions(self, score, features):
        """Generate recommended actions based on risk score and features."""
        actions = []
        
        if score >= 80:
            # Low risk - offer products and services
            possible_actions = [
                {
                    "action": "offer_credit_line_increase",
                    "description": "Offer increased credit limit",
                    "confidence": round(0.8 + 0.15 * random.random(), 2)
                },
                {
                    "action": "offer_premium_products",
                    "description": "Offer premium financial products",
                    "confidence": round(0.75 + 0.2 * random.random(), 2)
                },
                {
                    "action": "reduce_interest_rate",
                    "description": "Offer reduced interest rate",
                    "confidence": round(0.7 + 0.2 * random.random(), 2)
                }
            ]
            
            # Add 2 actions
            actions = random.sample(possible_actions, 2)
            
        elif score >= 60:
            # Medium risk - offer some products, some improvement suggestions
            possible_actions = [
                {
                    "action": "maintain_current_terms",
                    "description": "Maintain current credit terms",
                    "confidence": round(0.7 + 0.2 * random.random(), 2)
                },
                {
                    "action": "offer_financial_planning",
                    "description": "Offer financial planning services",
                    "confidence": round(0.65 + 0.2 * random.random(), 2)
                },
                {
                    "action": "suggest_debt_consolidation",
                    "description": "Suggest debt consolidation options",
                    "confidence": round(0.6 + 0.2 * random.random(), 2)
                }
            ]
            
            # Add 2 actions
            actions = random.sample(possible_actions, 2)
            
        else:
            # High or very high risk - suggest improvements
            possible_actions = [
                {
                    "action": "recommend_credit_counseling",
                    "description": "Recommend credit counseling service",
                    "confidence": round(0.8 + 0.15 * random.random(), 2)
                },
                {
                    "action": "suggest_payment_plan",
                    "description": "Suggest structured payment plan",
                    "confidence": round(0.75 + 0.2 * random.random(), 2)
                },
                {
                    "action": "offer_secured_credit",
                    "description": "Offer secured credit product",
                    "confidence": round(0.65 + 0.2 * random.random(), 2)
                },
                {
                    "action": "require_additional_verification",
                    "description": "Require additional income verification",
                    "confidence": round(0.7 + 0.2 * random.random(), 2)
                }
            ]
            
            # Add 2-3 actions
            actions = random.sample(possible_actions, random.randint(2, 3))
        
        return actions

class ProductRecommenderHandler(BaseMockMLHandler):
    """Handler for product recommendation model API."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self._send_json_response({
                "status": "healthy",
                "service": "product-recommender-model",
                "version": "1.0.0"
            })
        else:
            self._send_json_response({
                "message": "Product Recommendation API. Use POST /recommend for recommendations."
            })
    
    def do_POST(self):
        """Handle POST requests for ML model prediction."""
        if self.path == '/recommend':
            # Read request data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                # Parse JSON request
                request_data = json.loads(post_data)
                features = request_data.get('features', {})
                
                # Get customer ID or generate a placeholder
                customer_id = features.get('customer_id', f"unknown_{random.randint(1000, 9999)}")
                
                # Generate product recommendations
                recommendations = self._generate_recommendations(features)
                
                # Send response
                self._send_json_response(recommendations)
                
            except json.JSONDecodeError:
                self._send_json_response({"error": "Invalid JSON request"}, 400)
            except Exception as e:
                self._send_json_response({"error": f"Server error: {str(e)}"}, 500)
        else:
            self._send_json_response({"error": "Endpoint not found"}, 404)
    
    def _generate_recommendations(self, features):
        """Generate product recommendations based on customer features."""
        # Extract features with defaults
        customer_id = features.get('customer_id', 'unknown')
        preferred_categories = features.get('preferred_categories', '').split(',')
        recent_searches = features.get('recent_searches', '').split(',')
        price_sensitivity = features.get('price_sensitivity', 'medium')
        current_page = features.get('current_page', '')
        
        # Default to electronics if no categories provided
        if not preferred_categories or preferred_categories[0] == '':
            preferred_categories = ['electronics']
        
        # Generate context information
        context_sources = ["purchase_history"]
        if recent_searches and recent_searches[0]:
            context_sources.append("recent_searches")
        if current_page:
            context_sources.append("current_page")
            # Add current page to preferred categories if not already there
            if current_page not in preferred_categories:
                preferred_categories.append(current_page)
        
        # Add similar customers as a context source with 50% probability
        if random.random() > 0.5:
            context_sources.append("similar_customers")
        
        # Generate 3-5 recommendations
        num_recommendations = random.randint(3, 5)
        recommendations = []
        
        # First, generate recommendations based on preferred categories
        for i in range(num_recommendations):
            # Select a category, with higher probability for first few categories and current page
            category_weights = [1.0 / (idx + 1) for idx in range(len(preferred_categories))]
            # Double weight for current page if it's in the categories
            if current_page in preferred_categories:
                page_idx = preferred_categories.index(current_page)
                category_weights[page_idx] *= 2
            
            # Normalize weights
            total_weight = sum(category_weights)
            category_weights = [w / total_weight for w in category_weights]
            
            # Select category
            category = random.choices(preferred_categories, weights=category_weights)[0]
            
            # Generate product data
            product_id = f"prod_{random.randint(1000, 9999)}"
            
            # Price tier based on sensitivity
            if price_sensitivity == 'low':
                price_tier = random.choices(
                    ['premium', 'luxury', 'mid-range', 'budget'],
                    weights=[0.4, 0.3, 0.2, 0.1]
                )[0]
            elif price_sensitivity == 'high':
                price_tier = random.choices(
                    ['budget', 'mid-range', 'premium', 'luxury'],
                    weights=[0.5, 0.3, 0.15, 0.05]
                )[0]
            else:
                price_tier = random.choices(
                    ['mid-range', 'budget', 'premium', 'luxury'],
                    weights=[0.4, 0.3, 0.25, 0.05]
                )[0]
            
            # Product names based on category
            name_options = {
                'electronics': [
                    "Wireless Headphones", "Smartphone", "Laptop", "Smart Watch",
                    "Bluetooth Speaker", "Tablet", "Fitness Tracker", "Camera"
                ],
                'clothing': [
                    "T-Shirt", "Jeans", "Dress", "Shoes", "Jacket", "Sunglasses"
                ],
                'home': [
                    "Coffee Maker", "Blender", "Toaster", "Vacuum Cleaner", 
                    "Desk Lamp", "Air Purifier"
                ],
                'beauty': [
                    "Moisturizer", "Shampoo", "Perfume", "Makeup Kit",
                    "Face Mask", "Hair Dryer"
                ],
                'sports': [
                    "Yoga Mat", "Dumbbells", "Tennis Racket", "Backpack",
                    "Running Shoes", "Water Bottle"
                ]
            }
            
            # Get names for this category, default to electronics if category not found
            names = name_options.get(category, name_options['electronics'])
            name = random.choice(names)
            
            # Generate score, decreasing slightly for each subsequent recommendation
            # but with some randomness to make it realistic
            base_score = 0.98 - (i * 0.05)
            relevance_score = round(base_score - random.uniform(0, 0.1), 2)
            relevance_score = max(0.6, min(0.98, relevance_score))
            
            recommendations.append({
                "product_id": product_id,
                "name": name,
                "relevance_score": relevance_score,
                "price_tier": price_tier,
                "category": category
            })
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Create the response
        return {
            "customer_id": customer_id,
            "recommendations": recommendations,
            "context": {
                "current_page": current_page,
                "based_on": context_sources
            },
            "request_id": f"req_{random.randint(10000, 99999)}",
            "timestamp": datetime.now().isoformat()
        }

def run_server(handler_class, port):
    """Run an HTTP server with the specified handler on the given port."""
    server = HTTPServer(('localhost', port), handler_class)
    print(f"Starting {handler_class.__name__} on http://localhost:{port}")
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server, server_thread

def main():
    """Start the mock ML services."""
    parser = argparse.ArgumentParser(description="Run mock ML services for the generic orchestrator example")
    parser.add_argument("--credit-risk-port", type=int, default=5003, help="Port for the credit risk service")
    parser.add_argument("--recommender-port", type=int, default=5004, help="Port for the product recommender service")
    
    args = parser.parse_args()
    
    print("\n=== Starting Mock ML Services for Generic Orchestrator Example ===\n")
    
    # Start the credit risk service
    credit_server, credit_thread = run_server(CreditRiskHandler, args.credit_risk_port)
    
    # Start the product recommender service
    recommender_server, recommender_thread = run_server(ProductRecommenderHandler, args.recommender_port)
    
    print("\nAll services started successfully!")
    print("\nAvailable endpoints:")
    print(f"  Credit Risk API:         http://localhost:{args.credit_risk_port}/predict")
    print(f"  Product Recommender API: http://localhost:{args.recommender_port}/recommend")
    print("\nPress Ctrl+C to stop all services\n")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services...")
        credit_server.shutdown()
        recommender_server.shutdown()
        print("Services stopped")

if __name__ == "__main__":
    main()