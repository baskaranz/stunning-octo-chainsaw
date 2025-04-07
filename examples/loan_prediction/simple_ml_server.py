import http.server
import json
import socketserver
import sys

PORT = 5000

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"message": "Hello from Simple ML Server"}
        self.wfile.write(json.dumps(response).encode())
        print(f"GET request to {self.path}")
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        print(f"POST request to {self.path}")
        print(f"Headers: {self.headers}")
        print(f"Body: {post_data}")
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Always return the same response
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
        print(f"Response sent: {json.dumps(response)}")

# Create a server instance
if __name__ == "__main__":
    port = PORT
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    handler = SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    print(f"Starting server on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        httpd.server_close()