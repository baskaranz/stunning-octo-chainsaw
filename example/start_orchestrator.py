#!/usr/bin/env python3
"""
Start the Orchestrator API Service with the Iris Example configuration
"""
import os
import sys
import subprocess
import argparse
import time
import signal

# Set up paths
EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(EXAMPLE_DIR)

# Global variable for the orchestrator process
orchestrator_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C to stop orchestrator cleanly"""
    print("\nShutting down...")
    
    if orchestrator_process:
        print("Stopping orchestrator...")
        orchestrator_process.terminate()
        orchestrator_process.wait()
    
    print("Shutdown complete")
    sys.exit(0)

def start_orchestrator(port=8000, debug=False):
    """Start the orchestrator service"""
    global orchestrator_process
    
    # Set environment variables for configuration
    env = os.environ.copy()
    env['CONFIG_DIR'] = os.path.join(EXAMPLE_DIR, 'config')
    
    # Command to run the orchestrator
    orchestrator_cmd = [
        sys.executable, 
        os.path.join(PROJECT_ROOT, 'main.py'),
        '--port', str(port)
    ]
    
    if debug:
        orchestrator_cmd.append('--debug')
    
    print(f"Starting orchestrator with command: {' '.join(orchestrator_cmd)}")
    print(f"Using configuration directory: {env['CONFIG_DIR']}")
    
    # Start the orchestrator process
    orchestrator_process = subprocess.Popen(
        orchestrator_cmd,
        env=env,
        # Redirect output to our terminal
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Wait a moment for the orchestrator to start
    time.sleep(2)
    
    # Check if the process is still running
    if orchestrator_process.poll() is not None:
        print(f"Error: Orchestrator failed to start (exit code: {orchestrator_process.returncode})")
        sys.exit(1)
    
    print(f"Orchestrator started on port {port}")
    
    # Wait for the orchestrator process to finish
    try:
        orchestrator_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down orchestrator...")
        orchestrator_process.terminate()
        orchestrator_process.wait()
        print("Orchestrator stopped")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Start the Orchestrator API with Iris Example')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the orchestrator on (default: 8000)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Register signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the orchestrator
    start_orchestrator(port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()