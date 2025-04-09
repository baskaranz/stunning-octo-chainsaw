"""
Run the Iris Example with Local Model Loading
"""
import os
import subprocess
import sys
import time
import signal
import threading
import requests
import argparse
from iris_database import setup_database, get_iris_by_id, get_iris_sample

# Set up paths
EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXAMPLE_DIR))
CONFIG_DIR = os.path.join(EXAMPLE_DIR, 'config')
MODEL_PATH = os.path.join(EXAMPLE_DIR, 'models', 'iris_model.pkl')

# Model server process
model_server_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C to stop all processes cleanly"""
    print("\nShutting down...")
    
    if model_server_process:
        print("Stopping model server...")
        model_server_process.terminate()
        model_server_process.wait()
    
    print("Shutdown complete")
    sys.exit(0)

def setup():
    """Set up the example environment"""
    # Ensure model file exists
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file not found at {MODEL_PATH}")
        print("Please make sure you've copied the iris_model.pkl file to this location.")
        sys.exit(1)
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.join(CONFIG_DIR, 'domains', 'iris_example', 'integrations'), exist_ok=True)
    
    # Set up the database
    print("Setting up the iris database...")
    setup_database()
    print("Database setup complete!")

def start_model_server(model_port):
    """Start the model server in a subprocess"""
    print(f"Starting the Iris model server on port {model_port}...")
    global model_server_process
    
    # Set up environment variables
    env = os.environ.copy()
    env['MODEL_PATH'] = MODEL_PATH
    env['PORT'] = str(model_port)
    
    # Run the server
    model_server_process = subprocess.Popen(
        [sys.executable, os.path.join(EXAMPLE_DIR, 'iris_model_server.py')],
        env=env
    )
    
    # Wait for the server to start
    print("Waiting for model server to start...")
    max_retries = 10
    retries = 0
    server_ready = False
    
    while retries < max_retries and not server_ready:
        try:
            response = requests.get(f'http://localhost:{model_port}/health')
            if response.status_code == 200:
                server_ready = True
                print("Model server is ready!")
            else:
                retries += 1
                time.sleep(1)
        except requests.RequestException:
            retries += 1
            time.sleep(1)
    
    if not server_ready:
        print("Error: Model server failed to start!")
        sys.exit(1)

def test_direct_prediction(model_port):
    """Test the model server directly"""
    print("\nTesting direct model prediction...")
    
    # Get a sample iris flower
    sample = get_iris_sample(1)[0]
    
    # Prepare the features
    features = {
        'sepal_length': sample['sepal_length'],
        'sepal_width': sample['sepal_width'],
        'petal_length': sample['petal_length'],
        'petal_width': sample['petal_width']
    }
    
    # Make a prediction
    try:
        response = requests.post(
            f'http://localhost:{model_port}/predict',
            json={'features': features}
        )
        
        if response.status_code == 200:
            prediction = response.json()
            print(f"Sample features: {features}")
            print(f"Actual species: {sample['species']}")
            print(f"Predicted species: {prediction['prediction']['class_name']}")
            print(f"Prediction probabilities: {prediction['prediction']['probabilities']}")
        else:
            print(f"Error: {response.text}")
    except requests.RequestException as e:
        print(f"Error making prediction: {str(e)}")

def test_orchestrator_prediction(api_port):
    """Test prediction through the orchestrator"""
    print("\nTesting orchestrator prediction...")
    
    # Get a sample iris flower ID to test with
    sample = get_iris_sample(1)[0]
    flower_id = sample['id']
    
    print(f"Using flower ID: {flower_id} (Species: {sample['species']})")
    
    # Make a request to the orchestrator using the correct API path
    try:
        response = requests.get(
            f'http://localhost:{api_port}/orchestrator/iris_example/predict/{flower_id}'
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Orchestrator response:")
            print(f"  Features: {result.get('features', {})}")
            print(f"  Predicted species: {result.get('prediction', {}).get('class_name', 'unknown')}")
            print(f"  Probabilities: {result.get('prediction', {}).get('probabilities', {})}")
        else:
            print(f"Error from orchestrator: {response.text}")
    except requests.RequestException as e:
        print(f"Error calling orchestrator: {str(e)}")
        print("Make sure the orchestrator service is running. You can start it with:")
        print(f"  python main.py --config example/iris_example/config --port {api_port}")

def test_model_comparison(api_port):
    """Test the comparison endpoint that uses both loading methods"""
    print("\nTesting model comparison endpoint...")
    
    # Get a sample iris flower ID to test with
    sample = get_iris_sample(1)[0]
    flower_id = sample['id']
    
    print(f"Using flower ID: {flower_id} (Species: {sample['species']})")
    
    # Make a request to the orchestrator comparison endpoint with the correct API path
    # We need to access the 'compare' operation on the iris_example domain
    try:
        response = requests.get(
            f'http://localhost:{api_port}/orchestrator/iris_example/compare/{flower_id}'
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Comparison results:")
            print(f"  Features: {result.get('features', {})}")
            print("  HTTP model prediction:")
            http_pred = result.get('predictions', {}).get('http_model', {})
            print(f"    Species: {http_pred.get('class_name', 'unknown')}")
            
            print("  Local model prediction:")
            local_pred = result.get('predictions', {}).get('local_model', {})
            print(f"    Species: {local_pred.get('class_name', 'unknown')}")
            
            print("  Agreement:", "Yes" if http_pred.get('class_name') == local_pred.get('class_name') else "No")
        else:
            print(f"Error from orchestrator: {response.text}")
    except requests.RequestException as e:
        print(f"Error calling orchestrator: {str(e)}")
        print("Make sure the orchestrator service is running. You can start it with:")
        print(f"  python main.py --config example/iris_example/config --port {api_port}")

def show_help():
    """Display help information"""
    print("\nIris Example Usage:")
    print("  1. Start the model server and orchestrator separately:")
    print("     - Run this script to start the model server:")
    print("       python example/iris_example/run_iris_example.py --server [--model-port PORT]")
    print("     - In another terminal, start the generic orchestrator API with the Iris config:")
    print("       python main.py --config example/iris_example/config [--port PORT]")
    print("  2. Test the endpoints:")
    print("     - Direct model endpoint:")
    print("       python example/iris_example/run_iris_example.py --test-direct [--model-port PORT]")
    print("     - Orchestrator endpoint:")
    print("       python example/iris_example/run_iris_example.py --test-orchestrator [--api-port PORT]")
    print("     - Comparison endpoint:")
    print("       python example/iris_example/run_iris_example.py --test-comparison [--api-port PORT]")

def main():
    """Main function"""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Iris Example Runner')
    parser.add_argument('--server', action='store_true', help='Start the model server')
    parser.add_argument('--test-direct', action='store_true', help='Test the direct model endpoint')
    parser.add_argument('--test-orchestrator', action='store_true', help='Test the orchestrator endpoint')
    parser.add_argument('--test-comparison', action='store_true', help='Test the model comparison endpoint')
    parser.add_argument('--all', action='store_true', help='Run everything: start server, start orchestrator, and test all endpoints')
    parser.add_argument('--api-port', type=int, default=8000, help='Port for the Orchestrator API Service (default: 8000)')
    parser.add_argument('--model-port', type=int, default=8502, help='Port for the Iris model server (default: 8502)')
    args = parser.parse_args()
    
    # Ensure setup is done
    setup()
    
    # Parse the arguments for ports
    model_port = args.model_port
    api_port = args.api_port
    
    # Run everything if --all is specified
    if args.all:
        start_model_server(model_port)
        
        # Start the orchestrator in a subprocess
        print(f"Starting the generic Orchestrator API Service on port {api_port}...")
        orchestrator_process = subprocess.Popen(
            [sys.executable, os.path.join(PROJECT_ROOT, 'main.py'), 
             f'--port={api_port}', f'--config=example/iris_example/config']
        )
        
        # Wait a moment for the orchestrator to start
        time.sleep(3)
        
        # Run all tests
        test_direct_prediction(model_port)
        test_orchestrator_prediction(api_port)
        test_model_comparison(api_port)
        
        # Keep the script running
        print("\nAll tests completed. Services are still running.")
        print("Press Ctrl+C to stop all services.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            if orchestrator_process:
                orchestrator_process.terminate()
            if model_server_process:
                model_server_process.terminate()
        return
    
    # Start the model server if requested
    if args.server:
        start_model_server(model_port)
        print(f"Model server is running on port {model_port}. Press Ctrl+C to stop.")
        # Keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
    
    # Test direct model prediction
    if args.test_direct:
        start_model_server(model_port)
        test_direct_prediction(model_port)
        if model_server_process:
            model_server_process.terminate()
    
    # Test orchestrator prediction
    if args.test_orchestrator:
        test_orchestrator_prediction(api_port)
    
    # Test comparison
    if args.test_comparison:
        test_model_comparison(api_port)
    
    # If no specific action is requested, show help
    if len(sys.argv) == 1:
        show_help()

if __name__ == "__main__":
    main()