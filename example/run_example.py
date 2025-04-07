#!/usr/bin/env python3
"""
Generic Orchestrator Example - One-step Setup and Run

This script provides a simplified way to set up and run the generic orchestrator example.
It:
1. Creates and populates the database
2. Starts the mock ML services
3. Registers the database extensions
4. Sets up the ML configurations
5. Runs test queries against the orchestrator API

This approach avoids the need for extend_app.py and other complex extension mechanisms,
making the example more straightforward and focused on the configurations.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import threading
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import necessary modules
from app.adapters.database.database_client import DatabaseClient
from app.config.data_source_config_manager import DataSourceConfigManager

# Import database model and setup
from database_model import populate_database
from sqlalchemy import create_engine
import sqlite3

# Global variables for process management
ml_process = None
api_process = None
db_path = None

def setup_database():
    """Create and populate the example database."""
    print("Setting up the database...")
    
    # Determine the database path
    global db_path
    script_dir = Path(__file__).parent
    db_path = script_dir / "orchestrator_example.db"
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create the database directory if needed
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    # Create a SQLite database connection
    print(f"Creating new database at: {db_path}")
    connection_string = f"sqlite:///{db_path}"
    engine = create_engine(
        connection_string,
        connect_args={"check_same_thread": False}
    )
    
    # Populate the database with sample data
    populate_database(engine)
    
    print(f"✓ Database setup complete at: {db_path}")
    return str(db_path)

def start_ml_services():
    """Start the mock ML services in a subprocess."""
    print("Starting mock ML services...")
    
    global ml_process
    script_path = Path(__file__).parent / "mock_ml_services.py"
    
    # Start the process
    ml_process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for services to initialize (check if they're available)
    max_retries = 10
    retries = 0
    while retries < max_retries:
        try:
            # Check credit risk service
            response = requests.get("http://localhost:5003/health", timeout=1)
            if response.status_code == 200:
                # Check product recommender service
                response = requests.get("http://localhost:5004/health", timeout=1)
                if response.status_code == 200:
                    print("✓ Mock ML services started successfully")
                    return True
        except requests.exceptions.RequestException:
            pass
        
        retries += 1
        time.sleep(1)
        print(f"Waiting for ML services to start... (attempt {retries}/{max_retries})")
    
    print("⚠ Failed to start mock ML services")
    return False

def add_database_extensions():
    """Add database methods for the example."""
    print("Registering database extensions...")
    
    # Function to patch the DatabaseClient
    def patch_database_client():
        """Add methods for the generic orchestrator example to the DatabaseClient."""
        from database_extensions import patch_database_client
        patch_database_client()
    
    # Execute the function
    patch_database_client()
    print("✓ Database extensions registered")

def add_ml_configurations():
    """Add ML service configurations for the example."""
    print("Registering ML service configurations...")
    
    # Add credit risk model configuration
    DataSourceConfigManager.source_cache = getattr(DataSourceConfigManager, "source_cache", {})
    DataSourceConfigManager.source_cache["ml.credit_risk_model"] = {
        "base_url": "http://localhost:5003",
        "models": {
            "default": {
                "endpoint": "/predict",
                "timeout": 30,
                "headers": {
                    "Content-Type": "application/json"
                }
            }
        }
    }
    
    # Add product recommender model configuration
    DataSourceConfigManager.source_cache["ml.product_recommender"] = {
        "base_url": "http://localhost:5004",
        "models": {
            "default": {
                "endpoint": "/recommend",
                "timeout": 30,
                "headers": {
                    "Content-Type": "application/json"
                }
            }
        }
    }
    
    print("✓ ML service configurations registered")

def set_database_path():
    """Set the DatabaseClient to use our example database."""
    print("Configuring database connection...")
    
    # Patch the database client to use the example database
    original_init = DatabaseClient.__init__
    
    def patched_init(self, *args, **kwargs):
        # Call the original __init__ method
        original_init(self, *args, **kwargs)
        
        # Use our example database
        global db_path
        if db_path and os.path.exists(db_path):
            connection_string = f"sqlite:///{db_path}"
            from sqlalchemy import create_engine
            engine = create_engine(
                connection_string,
                connect_args={"check_same_thread": False}
            )
            self.engines["default"] = engine
            print(f"✓ Using example database at: {db_path}")
    
    # Apply the patch
    DatabaseClient.__init__ = patched_init

def run_api_server():
    """Run the API server in a subprocess."""
    print("Starting API server...")
    
    global api_process
    
    # Set environment variable for the example
    env = os.environ.copy()
    env["GENERIC_ORCHESTRATOR_EXAMPLE"] = "true"
    
    # Start the process with the --reload flag for development
    api_process = subprocess.Popen(
        [sys.executable, "main.py", "--reload"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the API to start
    max_retries = 10
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get("http://localhost:8000/docs", timeout=1)
            if response.status_code == 200:
                print("✓ API server started successfully")
                return True
        except requests.exceptions.RequestException:
            pass
        
        retries += 1
        time.sleep(1)
        print(f"Waiting for API server to start... (attempt {retries}/{max_retries})")
    
    print("⚠ Failed to start API server")
    return False

def call_credit_risk_api(customer_id, host="localhost", port=8000):
    """Call the credit risk API and return the result."""
    url = f"http://{host}:{port}/orchestrator/model_scoring/credit_risk/{customer_id}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling credit risk API: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

def call_product_recommender_api(customer_id, context=None, host="localhost", port=8000):
    """Call the product recommender API and return the result."""
    url = f"http://{host}:{port}/orchestrator/model_scoring/product_recommender/{customer_id}"
    
    try:
        if context:
            response = requests.post(url, json=context, timeout=5)
        else:
            response = requests.get(url, timeout=5)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling product recommender API: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

def run_examples():
    """Run example API calls to test the setup."""
    print("\nRunning example API calls...\n")
    
    # Test credit risk API
    print("1. Testing Credit Risk API:")
    credit_risk_result = call_credit_risk_api("cust_1001")
    if credit_risk_result:
        print(f"  ✓ Received credit risk assessment for {credit_risk_result.get('name')}")
        print(f"  ✓ Risk tier: {credit_risk_result.get('risk_score', {}).get('risk_tier')}")
        print(f"  ✓ Recommended actions: {len(credit_risk_result.get('recommended_actions', []))}")
    else:
        print("  ⚠ Credit risk API call failed")
    
    print("\n2. Testing Product Recommender API:")
    # Test product recommender API
    product_recommender_result = call_product_recommender_api(
        "cust_1002", 
        context={"current_page": "electronics"}
    )
    if product_recommender_result:
        recommendations = product_recommender_result.get('recommendations', [])
        print(f"  ✓ Received {len(recommendations)} product recommendations")
        if recommendations:
            print(f"  ✓ Top recommendation: {recommendations[0].get('name')}")
            print(f"  ✓ Relevance score: {recommendations[0].get('relevance_score')}")
    else:
        print("  ⚠ Product recommender API call failed")
    
    print("\nExample runs completed. The API server is still running.")
    print("You can now try your own API calls using the examples below.")

def print_usage_examples():
    """Print usage examples for manual testing."""
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES")
    print("=" * 60)
    
    print("\n1. Using curl:")
    print("   # Credit risk assessment")
    print("   curl \"http://localhost:8000/orchestrator/model_scoring/credit_risk/cust_1001\"")
    print("\n   # Product recommendations")
    print("   curl -X POST \"http://localhost:8000/orchestrator/model_scoring/product_recommender/cust_1002\" \\")
    print("     -H \"Content-Type: application/json\" \\")
    print("     -d '{\"current_page\": \"electronics\"}'")
    
    print("\n2. Using the API client:")
    print("   # Credit risk assessment")
    print("   python example/api_client.py credit-risk --id cust_1001")
    print("\n   # Product recommendations")
    print("   python example/api_client.py product-recommender --id cust_1002 \\")
    print("     --context current_page=electronics")
    
    print("\n3. Try with different customers:")
    print("   # Customers with different risk profiles")
    print("   curl \"http://localhost:8000/orchestrator/model_scoring/credit_risk/cust_1003\"")
    print("   curl \"http://localhost:8000/orchestrator/model_scoring/credit_risk/cust_1004\"")
    print("\n   # Customers with different preferences")
    print("   curl \"http://localhost:8000/orchestrator/model_scoring/product_recommender/cust_1003\"")
    print("   curl \"http://localhost:8000/orchestrator/model_scoring/product_recommender/cust_1005\"")
    
    print("\nPress Ctrl+C to stop all services\n")

def cleanup():
    """Clean up processes on exit."""
    print("\nCleaning up...")
    
    global ml_process, api_process
    
    if ml_process:
        ml_process.terminate()
        try:
            ml_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ml_process.kill()
    
    if api_process:
        api_process.terminate()
        try:
            api_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_process.kill()
    
    print("✓ All services stopped")

def main():
    """Main function to set up and run the example."""
    parser = argparse.ArgumentParser(description="Set up and run the generic orchestrator example")
    parser.add_argument("--no-run", action="store_true", help="Set up services but don't run example API calls")
    
    args = parser.parse_args()
    
    try:
        # Register signal handler for clean shutdown
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
        
        print("\n" + "=" * 60)
        print("GENERIC ORCHESTRATOR EXAMPLE SETUP")
        print("=" * 60 + "\n")
        
        # Set up the components
        db_path = setup_database()
        if not start_ml_services():
            print("Failed to start mock ML services. Exiting.")
            return 1
        
        # Register database extensions and ML configurations
        add_database_extensions()
        add_ml_configurations()
        set_database_path()
        
        # Start the API server
        if not run_api_server():
            print("Failed to start API server. Exiting.")
            return 1
        
        # Run the examples if not disabled
        if not args.no_run:
            time.sleep(2)  # Give the API server a moment to fully initialize
            run_examples()
        
        # Print usage examples
        print_usage_examples()
        
        # Keep the script running until interrupted
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())