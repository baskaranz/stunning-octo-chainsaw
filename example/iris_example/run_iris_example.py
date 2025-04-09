"""
Run the Iris Example with Local Model Loading
"""
import os
import subprocess
import sys
import time
import signal
import requests
import argparse
from iris_database import setup_database, get_iris_by_id, get_iris_sample

# Set up paths
EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXAMPLE_DIR))
MODELS_DIR = os.path.join(EXAMPLE_DIR, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'iris_model.pkl')

# Global variables
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
    print("📦 Setting up the Iris Example environment...")
    
    # Ensure model file exists
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file not found at {MODEL_PATH}")
        print("Please make sure you've copied the iris_model.pkl file to this location.")
        sys.exit(1)
    
    # Create model and database directories if needed
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Import here to get the updated path
    from iris_database import IRIS_DB_PATH
    
    # Set up the database
    print(f"🔧 Creating the iris database at {IRIS_DB_PATH}...")
    setup_database()
    print("✅ Database setup complete!")
    
    # Copy config files to main config directory
    print("🔧 Installing configuration files...")
    install_config_files()
    print("✅ Configuration installed in main config directory.")
    
    # Display next steps
    print("\n🎉 Setup complete! Next steps:")
    print("1. Start the model server:")
    print("   python example/iris_example/run_iris_example.py --server")
    print("2. Start the orchestrator service (or restart it if already running):")
    print("   python main.py")
    print("3. Test the endpoints:")
    print("   python example/iris_example/run_iris_example.py --test-orchestrator")
    print("\nTo check if the orchestrator has loaded the iris domain:")
    print("   python example/iris_example/run_iris_example.py --check-orchestrator")

def install_config_files():
    """Copy configuration files to the main config directory"""
    # Create domain directory structure in main config
    domain_dir = os.path.join(PROJECT_ROOT, 'config', 'domains', 'iris_example')
    domain_int_dir = os.path.join(domain_dir, 'integrations')
    os.makedirs(domain_int_dir, exist_ok=True)
    
    # Define source and destination paths
    example_config_dir = os.path.join(EXAMPLE_DIR, 'config')
    src_domain_yaml = os.path.join(example_config_dir, 'domains', 'iris_example.yaml')
    src_db_yaml = os.path.join(example_config_dir, 'domains', 'iris_example', 'database.yaml')
    src_ml_yaml = os.path.join(example_config_dir, 'domains', 'iris_example', 'integrations', 'ml_config.yaml')
    
    dst_domain_yaml = os.path.join(PROJECT_ROOT, 'config', 'domains', 'iris_example.yaml')
    dst_db_yaml = os.path.join(domain_dir, 'database.yaml')
    dst_ml_yaml = os.path.join(domain_int_dir, 'ml_config.yaml')
    
    # Copy files if they exist
    for src, dst in [(src_domain_yaml, dst_domain_yaml), 
                     (src_db_yaml, dst_db_yaml), 
                     (src_ml_yaml, dst_ml_yaml)]:
        if os.path.exists(src):
            with open(src, 'r') as src_file:
                content = src_file.read()
                
            with open(dst, 'w') as dst_file:
                dst_file.write(content)
            
            print(f"Copied {os.path.basename(src)} to {os.path.relpath(dst, PROJECT_ROOT)}")

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
        print(f"Sending request to: http://localhost:{api_port}/orchestrator/iris_example/predict/{flower_id}")
        response = requests.get(
            f'http://localhost:{api_port}/orchestrator/iris_example/predict/{flower_id}'
        )
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Orchestrator response:")
            print(f"  Features: {result.get('features', {})}")
            print(f"  Predicted species: {result.get('prediction', {}).get('class_name', 'unknown')}")
            print(f"  Probabilities: {result.get('prediction', {}).get('probabilities', {})}")
        elif response.status_code == 404:
            print("❌ Endpoint not found. This suggests the iris_example domain is not properly loaded.")
            print("   Please try the following steps:")
            print("   1. Make sure you've run setup: python example/iris_example/run_iris_example.py --setup")
            print("   2. Restart the orchestrator: python main.py")
            print("   3. Check status: python example/iris_example/run_iris_example.py --check-orchestrator")
        else:
            print(f"Error from orchestrator: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Error calling orchestrator: {str(e)}")
        print("Make sure the orchestrator service is running. You can start it with:")
        print(f"  python main.py --port {api_port}")

def test_model_comparison(api_port):
    """Test the comparison endpoint that uses both loading methods"""
    print("\nTesting model comparison endpoint...")
    
    # Get a sample iris flower ID to test with
    sample = get_iris_sample(1)[0]
    flower_id = sample['id']
    
    print(f"Using flower ID: {flower_id} (Species: {sample['species']})")
    
    # Make a request to the orchestrator comparison endpoint with the correct API path
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
        print(f"  python main.py --port {api_port}")

def check_orchestrator(api_port):
    """Check if the orchestrator is running and has loaded the iris domain"""
    try:
        # First try to get list of domains
        response = requests.get(f'http://localhost:{api_port}/orchestrator/domains')
        if response.status_code == 200:
            domains = response.json()
            if 'iris_example' in domains:
                print("✅ Orchestrator is running and has loaded the iris_example domain!")
                return True
            else:
                print("❌ Orchestrator is running but has not loaded the iris_example domain.")
                print("   This may be because:")
                print("   1. You need to run the setup step first: python example/iris_example/run_iris_example.py --setup")
                print("   2. You need to restart the orchestrator to load the new configuration")
                print("      python main.py")
                return False
        else:
            print(f"⚠️ Domains endpoint returned: {response.status_code} - {response.text}")
            print("Trying direct endpoint check instead...")
            
            # If domains endpoint isn't working, try accessing an iris endpoint directly
            try:
                # Try to access a sample endpoint
                test_response = requests.get(f'http://localhost:{api_port}/orchestrator/iris_example/samples?limit=1')
                if test_response.status_code == 200:
                    print("✅ Orchestrator is running and iris_example domain is accessible!")
                    return True
                elif test_response.status_code == 404:
                    print("❌ Iris example endpoints not found. Domain may not be loaded.")
                    print("   This may be because:")
                    print("   1. You need to run the setup step first: python example/iris_example/run_iris_example.py --setup")
                    print("   2. You need to restart the orchestrator to load the new configuration")
                    print("      python main.py")
                    return False
                else:
                    print(f"❌ Error testing iris endpoint: {test_response.status_code} - {test_response.text}")
                    return False
            except requests.RequestException as e:
                print(f"❌ Error testing iris endpoint: {str(e)}")
                return False
    except requests.RequestException as e:
        print(f"❌ Orchestrator does not appear to be running: {str(e)}")
        print(f"   Please start it with: python main.py --port {api_port}")
        return False

def show_help():
    """Display help information"""
    print("\nIris Example Usage:")
    print("  1. Setup and configuration:")
    print("     - Set up the example (database and configs):")
    print("       python example/iris_example/run_iris_example.py --setup")
    print("  2. Run the components:")
    print("     - Start the model server:")
    print("       python example/iris_example/run_iris_example.py --server [--model-port PORT]")
    print("     - In another terminal, make sure the standard orchestrator API is running:")
    print("       python main.py [--port PORT]")
    print("  3. Test the endpoints:")
    print("     - Direct model endpoint:")
    print("       python example/iris_example/run_iris_example.py --test-direct [--model-port PORT]")
    print("     - Orchestrator endpoint:")
    print("       python example/iris_example/run_iris_example.py --test-orchestrator [--api-port PORT]")
    print("     - Comparison endpoint:")
    print("       python example/iris_example/run_iris_example.py --test-comparison [--api-port PORT]")
    print("  4. Check if orchestrator has loaded the iris domain:")
    print("       python example/iris_example/run_iris_example.py --check-orchestrator [--api-port PORT]")

def test_domains_endpoint(api_port):
    """Test the domains endpoint directly"""
    print("\nTesting /orchestrator/domains endpoint...")
    
    try:
        response = requests.get(f"http://localhost:{api_port}/orchestrator/domains")
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            print(f"Response content: {response.text}")
            try:
                print(f"JSON response: {response.json()}")
            except Exception as e:
                print(f"Error parsing JSON: {e}")
        else:
            print(f"Error response: {response.text}")
    except requests.RequestException as e:
        print(f"Request error: {e}")
        
    # Also test the endpoints directly
    print("\nTesting direct endpoint access...")
    endpoints = [
        f"http://localhost:{api_port}/orchestrator/iris_example/samples?limit=1",
        f"http://localhost:{api_port}/orchestrator/iris_example/predict/1",
        f"http://localhost:{api_port}/orchestrator/iris_example/predict_local/1",
        f"http://localhost:{api_port}/orchestrator/iris_example/compare/1"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTrying: {endpoint}")
            response = requests.get(endpoint)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("SUCCESS! Endpoint is working")
                print(f"Response body: {response.text[:100]}...")
            else:
                print(f"Error: {response.text}")
        except requests.RequestException as e:
            print(f"Error: {e}")

def main():
    """Main function"""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Iris Example Runner')
    parser.add_argument('--setup', action='store_true', help='Set up the example environment')
    parser.add_argument('--server', action='store_true', help='Start the model server')
    parser.add_argument('--test-direct', action='store_true', help='Test the direct model endpoint')
    parser.add_argument('--test-orchestrator', action='store_true', help='Test the orchestrator endpoint')
    parser.add_argument('--test-comparison', action='store_true', help='Test the model comparison endpoint')
    parser.add_argument('--check-orchestrator', action='store_true', help='Check if orchestrator is running with iris domain')
    parser.add_argument('--test-domains', action='store_true', help='Test the domains endpoint')
    parser.add_argument('--api-port', type=int, default=8000, help='Port for the Orchestrator API Service (default: 8000)')
    parser.add_argument('--model-port', type=int, default=8502, help='Port for the Iris model server (default: 8502)')
    args = parser.parse_args()
    
    # Parse the arguments for ports
    model_port = args.model_port
    api_port = args.api_port
    
    # Set up if requested
    if args.setup:
        setup()
        return
    
    # Check orchestrator
    if args.check_orchestrator:
        check_orchestrator(api_port)
        return
        
    # Test domains endpoint
    if args.test_domains:
        test_domains_endpoint(api_port)
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
        if check_orchestrator(api_port):
            test_orchestrator_prediction(api_port)
    
    # Test comparison
    if args.test_comparison:
        if check_orchestrator(api_port):
            test_model_comparison(api_port)
    
    # If no specific action is requested, show help
    if len(sys.argv) == 1:
        show_help()

if __name__ == "__main__":
    main()