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
import socket
import requests
import atexit

# Set up paths
EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(EXAMPLE_DIR)

# Global variable for the orchestrator process
orchestrator_process = None

def cleanup():
    """Cleanup function to ensure process is terminated"""
    global orchestrator_process
    if orchestrator_process and orchestrator_process.poll() is None:
        print("\nCleaning up orchestrator process...")
        try:
            orchestrator_process.terminate()
            try:
                orchestrator_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                print("Force killing orchestrator process...")
                if sys.platform.startswith('win'):
                    subprocess.call(f'taskkill /F /PID {orchestrator_process.pid}', shell=True)
                else:
                    os.kill(orchestrator_process.pid, signal.SIGKILL)
        except Exception as e:
            print(f"Error during cleanup: {e}")

# Register the cleanup function
atexit.register(cleanup)

def signal_handler(sig, frame):
    """Handle Ctrl+C to stop orchestrator cleanly"""
    print("\nShutting down...")
    
    global orchestrator_process
    if orchestrator_process:
        print("Stopping orchestrator...")
        try:
            # Try graceful termination first
            orchestrator_process.terminate()
            # Wait only briefly for graceful termination
            for _ in range(3):
                if orchestrator_process.poll() is not None:
                    break
                time.sleep(0.5)
            
            # If still running, force kill
            if orchestrator_process.poll() is None:
                print("Orchestrator not responding to graceful termination. Forcing shutdown...")
                if sys.platform.startswith('win'):
                    # Windows doesn't have SIGKILL
                    subprocess.call(f'taskkill /F /PID {orchestrator_process.pid}', shell=True)
                else:
                    # Linux/Mac
                    import signal
                    os.kill(orchestrator_process.pid, signal.SIGKILL)
        except Exception as e:
            print(f"Error during shutdown: {e}")
    
    # Find any other Python processes that might be related to our server
    try:
        print("Checking for other Python server processes...")
        if sys.platform.startswith('win'):
            pass # Windows handling would go here
        else:
            # On Mac/Linux, find Python processes
            pids = subprocess.check_output("ps aux | grep 'python.*main.py' | grep -v grep | awk '{print $2}'", shell=True).decode().strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        pid = int(pid)
                        print(f"Killing Python process with PID {pid}")
                        os.kill(pid, signal.SIGKILL)
                    except Exception as e:
                        print(f"Could not kill process {pid}: {e}")
    except Exception as e:
        print(f"Error cleaning up processes: {e}")
    
    print("Shutdown complete")
    # Force exit to make sure everything stops
    os._exit(0)

def check_port_in_use(port):
    """Check if a port is in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """Kill the process using the specified port"""
    if sys.platform.startswith('win'):
        # Windows
        try:
            output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            if output:
                # The last number in the output is the PID
                pid = output.strip().split()[-1]
                subprocess.call(f'taskkill /F /PID {pid}', shell=True)
                print(f"Killed process with PID {pid} using port {port}")
                # Give the system time to release the port
                time.sleep(1)
                return True
            return False
        except subprocess.CalledProcessError:
            return False
    else:
        # Mac/Linux
        try:
            cmd = f"lsof -i :{port} | grep LISTEN | awk '{{print $2}}'"
            pid = subprocess.check_output(cmd, shell=True).decode().strip()
            if pid:
                subprocess.call(f'kill -9 {pid}', shell=True)
                print(f"Killed process with PID {pid} using port {port}")
                # Give the system time to release the port
                time.sleep(1)
                return True
            return False
        except subprocess.CalledProcessError:
            return False

def start_orchestrator(port=8000, debug=False):
    """Start the orchestrator service"""
    global orchestrator_process
    
    # Check if port is already in use
    if check_port_in_use(port):
        print(f"Port {port} is already in use.")
        print("Attempting to kill the process using this port...")
        if kill_process_on_port(port):
            print(f"Successfully freed port {port}.")
            # Give the system time to fully release the port
            time.sleep(1)  
        else:
            alternative_port = port + 1
            print(f"Could not free port {port}. Trying alternative port {alternative_port}...")
            
            # If alternative port is also in use, try to kill that process as well
            if check_port_in_use(alternative_port):
                if kill_process_on_port(alternative_port):
                    print(f"Successfully freed port {alternative_port}.")
                else:
                    print(f"Could not free port {alternative_port}. Please manually check which process is using these ports.")
                    sys.exit(1)
            
            port = alternative_port
    
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
    
    # Try to make a request to verify it's responding
    try:
        response = requests.get(f"http://localhost:{port}/docs")
        if response.status_code == 200:
            print(f"✅ Orchestrator is up and running on port {port}")
            print(f"   Try the Swagger UI at: http://localhost:{port}/docs")
        else:
            print(f"⚠️ Orchestrator might be running but returned status code {response.status_code}")
    except requests.RequestException:
        print("⚠️ Orchestrator process started but is not responding to HTTP requests yet")
        print("   This might be normal if the server is still initializing")
    
    # Wait for the orchestrator process to finish
    try:
        # Use a polling approach with small timeout so we can catch keyboard interrupts
        while orchestrator_process.poll() is None:
            try:
                # Wait for a small amount of time
                exit_code = orchestrator_process.wait(timeout=0.5)
                print(f"Orchestrator process exited with code {exit_code}")
                break
            except subprocess.TimeoutExpired:
                # Process still running, continue polling
                continue
    except KeyboardInterrupt:
        # This block is likely not used since we have a signal handler,
        # but keeping it as a fallback
        print("\nShutting down orchestrator...")
        try:
            orchestrator_process.terminate()
            orchestrator_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            print("Orchestrator not responding to termination. Forcing...")
            if sys.platform.startswith('win'):
                subprocess.call(f'taskkill /F /PID {orchestrator_process.pid}', shell=True)
            else:
                os.kill(orchestrator_process.pid, signal.SIGKILL)
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