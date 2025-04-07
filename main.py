#!/usr/bin/env python3

import os
import argparse
import uvicorn
from app import create_app

# Create the base app
app = create_app()

# Check if we should include the loan prediction example
if os.environ.get('LOAN_PREDICTION_EXAMPLE', '').lower() in ('true', '1', 'yes'):
    try:
        from examples.loan_prediction.extend_app import extend_app
        app = extend_app(app)
        print("✓ Loan Prediction example functionality enabled")
    except ImportError as e:
        print(f"⚠ Failed to load loan prediction example: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Orchestrator API Service")
    parser.add_argument("--port", type=int, default=8000, help="Port number to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    
    # Add examples flag
    parser.add_argument("--with-loan-prediction", action="store_true", 
                       help="Enable the loan prediction example functionality")
    
    args = parser.parse_args()
    
    # Set environment variable if flag is used
    if args.with_loan_prediction:
        os.environ['LOAN_PREDICTION_EXAMPLE'] = 'true'
        
        # If running with loan prediction but no config path specified,
        # default to the example config path
        if 'ORCHESTRATOR_CONFIG_PATH' not in os.environ:
            example_config_path = os.path.join(os.getcwd(), "examples/loan_prediction/config")
            os.environ['ORCHESTRATOR_CONFIG_PATH'] = example_config_path
            print(f"Using loan prediction config path: {example_config_path}")
    
    # Run the server
    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)
