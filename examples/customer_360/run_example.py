#!/usr/bin/env python3
"""
Run Customer 360 Example

This script provides an easy way to run the Customer 360 example from start to finish.
It handles:
1. Setting up the database
2. Starting the orchestrator API service
3. Running the example with a customer ID
4. Gracefully stopping the service when done
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
    """Set up the SQLite database for the Customer 360 example."""
    print("\n=== Setting up the database ===")
    setup_script = PROJECT_ROOT / "examples" / "customer_360" / "setup_database.py"
    
    result = subprocess.run(
        [sys.executable, str(setup_script)],
        check=False
    )
    
    if result.returncode != 0:
        print("Error setting up the database. Exiting.")
        sys.exit(1)
    
    print("Database setup complete.")

def start_service(port=8000):
    """Start the orchestrator API service with the example configuration."""
    print(f"\n=== Starting orchestrator API service on port {port} ===")
    
    # Build the environment with the config path
    env = os.environ.copy()
    config_path = PROJECT_ROOT / "examples" / "customer_360" / "config"
    env["ORCHESTRATOR_CONFIG_PATH"] = str(config_path)
    
    # Start the service in the background
    process = subprocess.Popen(
        [
            "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", str(port),
            "--app-dir", str(PROJECT_ROOT)
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        cwd=str(PROJECT_ROOT)
    )
    
    # Wait for the service to start
    print("Waiting for service to start...")
    time.sleep(3)
    
    # Check if the process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"Error starting service: {stderr}")
        sys.exit(1)
    
    print(f"Service started with PID {process.pid}")
    return process

def run_example(customer_id, port=8000):
    """Run the Customer 360 example with the given customer ID."""
    print(f"\n=== Running Customer 360 example for customer {customer_id} ===")
    
    example_script = PROJECT_ROOT / "examples" / "customer_360" / "get_customer_360.py"
    
    # We need to temporarily modify the script to use the correct port if it's not 8000
    port_env = {}
    if port != 8000:
        port_env["ORCHESTRATOR_PORT"] = str(port)
    
    result = subprocess.run(
        [sys.executable, str(example_script), customer_id],
        env={**os.environ, **port_env},
        check=False
    )
    
    if result.returncode != 0:
        print(f"Error running example for customer {customer_id}.")
        return False
    
    return True

def gracefully_stop_service(process):
    """Gracefully stop the orchestrator API service."""
    print("\n=== Stopping orchestrator API service ===")
    
    if process is None or process.poll() is not None:
        print("Service is not running.")
        return
    
    # Send SIGTERM signal for graceful shutdown
    process.send_signal(signal.SIGTERM)
    
    # Wait for process to terminate
    try:
        process.wait(timeout=5)
        print("Service stopped successfully.")
    except subprocess.TimeoutExpired:
        print("Service didn't stop within the timeout period.")
        print("Forcefully terminating...")
        process.kill()
        print("Service forcefully terminated.")

def main():
    parser = argparse.ArgumentParser(description="Run the Customer 360 example")
    parser.add_argument(
        "--customer", "-c", 
        default="cust_12345",
        help="Customer ID to use for the example (default: cust_12345)"
    )
    parser.add_argument(
        "--port", "-p", 
        type=int, 
        default=8000,
        help="Port to run the orchestrator API service on (default: 8000)"
    )
    parser.add_argument(
        "--skip-db-setup", 
        action="store_true",
        help="Skip database setup step"
    )
    
    args = parser.parse_args()
    
    try:
        # Setup the database (unless skipped)
        if not args.skip_db_setup:
            setup_database()
        
        # Start the service
        service_process = start_service(port=args.port)
        
        try:
            # Run the example
            run_example(args.customer, port=args.port)
        finally:
            # Always stop the service gracefully
            gracefully_stop_service(service_process)
        
        print("\n=== Example completed successfully ===")
        print(f"To run again with a different customer, try:")
        print(f"python {__file__} --customer cust_67890 --skip-db-setup")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()