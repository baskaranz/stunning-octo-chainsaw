#!/usr/bin/env python3
"""
Run Loan Prediction Example

This script provides an easy way to run the Loan Prediction example from start to finish.
It handles:
1. Setting up the database
2. Starting the mock ML service
3. Starting the orchestrator API service
4. Running the example with an applicant ID
5. Gracefully stopping the services when done
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Get the absolute path to the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()

def setup_database():
    """Set up the SQLite database for the Loan Prediction example."""
    print("\n=== Setting up the database ===")
    setup_script = PROJECT_ROOT / "examples" / "loan_prediction" / "setup_database.py"
    
    result = subprocess.run(
        [sys.executable, str(setup_script)],
        check=False
    )
    
    if result.returncode != 0:
        print("Error setting up the database. Exiting.")
        sys.exit(1)
    
    print("Database setup complete.")

def start_ml_service(port=5000):
    """Start the mock ML service."""
    print("\n=== Starting mock ML service ===")
    ml_service_script = PROJECT_ROOT / "examples" / "loan_prediction" / "mock_ml_service.py"
    
    # Start the ML service in a new process
    process = subprocess.Popen(
        [sys.executable, str(ml_service_script), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the service a moment to start
    time.sleep(2)
    
    if process.poll() is not None:
        print("Error starting mock ML service. Exiting.")
        sys.exit(1)
    
    print(f"Mock ML service started on port {port}")
    return process

def start_service(port=8000):
    """Start the orchestrator API service with the example configuration."""
    print("\n=== Starting orchestrator API service ===")
    
    # Set the configuration path to use example configs
    env = os.environ.copy()
    env["ORCHESTRATOR_CONFIG_PATH"] = str(PROJECT_ROOT / "examples" / "loan_prediction" / "config")
    
    # Start the service in a new process
    process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "main.py"), "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the service a moment to start
    time.sleep(3)
    
    if process.poll() is not None:
        print("Error starting orchestrator API service. Exiting.")
        sys.exit(1)
    
    print(f"Orchestrator API service started on port {port}")
    return process

def run_example(applicant_id, port=8000):
    """Run the Loan Prediction example with the given applicant ID."""
    print(f"\n=== Running Loan Prediction example for applicant {applicant_id} ===")
    
    example_script = PROJECT_ROOT / "examples" / "loan_prediction" / "get_loan_prediction.py"
    
    # We need to temporarily modify the script to use the correct port if it's not 8000
    port_env = {}
    if port != 8000:
        port_env["ORCHESTRATOR_PORT"] = str(port)
    
    result = subprocess.run(
        [sys.executable, str(example_script), applicant_id, "--port", str(port)],
        env={**os.environ, **port_env},
        check=False
    )
    
    if result.returncode != 0:
        print(f"Error running example for applicant {applicant_id}.")
        return False
    
    return True

def gracefully_stop_services(services):
    """Gracefully stop the orchestrator API service and mock ML service."""
    print("\n=== Stopping services ===")
    
    for service in services:
        if service and service.poll() is None:
            if sys.platform == "win32":
                service.send_signal(signal.CTRL_C_EVENT)
            else:
                service.terminate()
            
            # Give the service time to shut down gracefully
            try:
                service.wait(timeout=5)
            except subprocess.TimeoutExpired:
                service.kill()
    
    print("All services stopped.")

def main():
    parser = argparse.ArgumentParser(description="Run the Loan Prediction example")
    parser.add_argument(
        "--applicant", "-a", 
        default="app_1001",
        help="Applicant ID to use for the example (default: app_1001)"
    )
    parser.add_argument(
        "--port", "-p", 
        type=int, 
        default=8000,
        help="Port to run the orchestrator API service on (default: 8000)"
    )
    parser.add_argument(
        "--ml-port", 
        type=int, 
        default=5000,
        help="Port to run the mock ML service on (default: 5000)"
    )
    parser.add_argument(
        "--skip-db-setup", 
        action="store_true",
        help="Skip database setup step"
    )
    
    args = parser.parse_args()
    
    services = []
    
    try:
        # Setup the database (unless skipped)
        if not args.skip_db_setup:
            setup_database()
        
        # Start the ML service
        ml_service = start_ml_service(port=args.ml_port)
        services.append(ml_service)
        
        # Start the API service
        api_service = start_service(port=args.port)
        services.append(api_service)
        
        try:
            # Run the example
            run_example(args.applicant, port=args.port)
        finally:
            # Always stop the services gracefully
            gracefully_stop_services(services)
        
        print("\n=== Example completed successfully ===")
        print(f"To run again with a different applicant, try:")
        print(f"python {__file__} --applicant app_1002 --skip-db-setup")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        gracefully_stop_services(services)
        sys.exit(1)

if __name__ == "__main__":
    main()