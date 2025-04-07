#!/usr/bin/env python3
"""
Loan Prediction Example - Super Simple Mock ML Service
"""

import argparse
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class MockServiceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        print(f"GET request to {self.path}")
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Hello from ML service"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        print(f"POST request to {self.path}")
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            post_data = self.rfile.read(content_length).decode('utf-8')
            print(f"Request body: {post_data}")
        
        # Always return a successful response with dummy data
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Dummy loan prediction response
        response = {
            "probability": 0.75,
            "decision": "Approved",
            "risk_tier": "Moderate Risk",
            "suggested_interest_rate": 5.5,
            "factors": {
                "credit_score": {"value": 720, "impact": 0.8, "weight": 0.4},
                "debt_to_income": {"value": 0.28, "impact": 0.7, "weight": 0.3},
                "income_vs_loan": {"value": "$75000 / $250000", "impact": 0.6, "weight": 0.2},
                "employment_history": {"value": "5 years", "impact": 0.9, "weight": 0.1}
            }
        }
        
        self.wfile.write(json.dumps(response).encode())

def main():
    parser = argparse.ArgumentParser(description='Run simple mock ML service')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()
    
    server = HTTPServer(('localhost', args.port), MockServiceHandler)
    print(f"Starting mock ML service on http://localhost:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    
    server.server_close()

if __name__ == "__main__":
    main()