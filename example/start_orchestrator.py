#!/usr/bin/env python
"""
Start the Orchestrator API Service with explicit port configuration
for the Iris Example
"""
import os
import sys
import importlib.util
import uvicorn
import argparse
import subprocess
import time
import signal

# Add project root to path to allow imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def check_port_in_use(port):
    """Check if the specified port is already in use"""
    try:
        result = subprocess.run(['lsof', '-i', f':{port}'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, 
                             text=True)
        return result.returncode == 0  # If the command returns 0, the port is in use
    except Exception:
        # If lsof command fails, we can't determine if port is in use
        return False

def stop_process_on_port(port):
    """Stop any process running on the specified port"""
    try:
        # Get the PID of the process using the port
        result = subprocess.run(['lsof', '-t', '-i', f':{port}'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, 
                             text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            if pid:
                print(f"Stopping process (PID: {pid}) running on port {port}...")
                # Send SIGTERM signal to gracefully terminate the process
                subprocess.run(['kill', pid])
                # Wait a moment for the process to stop
                time.sleep(1)
                return True
    except Exception as e:
        print(f"Error stopping process on port {port}: {e}")
    return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start the Orchestrator API Service for Iris Example')
    parser.add_argument('--api-port', type=int, default=8088, help='Port for the Orchestrator API Service (default: 8088)')
    parser.add_argument('--model-port', type=int, default=8502, help='Port for the Iris model server (default: 8502)')
    args = parser.parse_args()
    
    # Check if ports are already in use and stop any running processes
    if check_port_in_use(args.api_port):
        print(f"Port {args.api_port} is already in use.")
        if stop_process_on_port(args.api_port):
            print(f"Successfully stopped the process using port {args.api_port}")
        else:
            print(f"Failed to stop the process. Please stop it manually.")
            sys.exit(1)
    
    # Set environment variables for configuration and model port
    os.environ["CONFIG_PATH"] = "example/iris_example/config"
    os.environ["MODEL_PORT"] = str(args.model_port)
    
    print("Starting Orchestrator API Service for Iris Example...")
    print(f"Using config path: {os.environ['CONFIG_PATH']}")
    print(f"API port: {args.api_port}")
    print(f"Model port: {args.model_port}")
    
    # Create the FastAPI app
    spec = importlib.util.spec_from_file_location("app_module", os.path.join(project_root, "app", "__init__.py"))
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    app = app_module.create_app()
    
    # Run the app with the specified port
    uvicorn.run(app, host="0.0.0.0", port=args.api_port)