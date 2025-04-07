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

# Check if we should include the churn prediction example
if os.environ.get('CHURN_PREDICTION_EXAMPLE', '').lower() in ('true', '1', 'yes'):
    try:
        from examples.churn_prediction.extend_app import extend_app
        app = extend_app(app)
        print("✓ Customer Churn Prediction example functionality enabled")
    except ImportError as e:
        print(f"⚠ Failed to load churn prediction example: {e}")

# Generic orchestrator example doesn't need extensions since it uses configuration only
# Just print a notice if the flag is enabled
if os.environ.get('GENERIC_ORCHESTRATOR_EXAMPLE', '').lower() in ('true', '1', 'yes'):
    print("✓ Generic Orchestrator example functionality enabled")
    print("  Note: This example uses configuration-only approach, no code extensions needed")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Orchestrator API Service")
    parser.add_argument("--port", type=int, default=8000, help="Port number to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    
    # Add examples flags
    parser.add_argument("--with-loan-prediction", action="store_true", 
                       help="Enable the loan prediction example functionality")
    parser.add_argument("--with-churn-prediction", action="store_true",
                       help="Enable the customer churn prediction example functionality")
    parser.add_argument("--with-generic-orchestrator", action="store_true",
                       help="Enable the generic orchestrator example functionality")
    
    args = parser.parse_args()
    
    # Set environment variables if flags are used
    if args.with_loan_prediction:
        os.environ['LOAN_PREDICTION_EXAMPLE'] = 'true'
        
        # If running with loan prediction but no config path specified,
        # default to the example config path
        if 'ORCHESTRATOR_CONFIG_PATH' not in os.environ:
            example_config_path = os.path.join(os.getcwd(), "examples/loan_prediction/config")
            os.environ['ORCHESTRATOR_CONFIG_PATH'] = example_config_path
            print(f"Using loan prediction config path: {example_config_path}")
    
    if args.with_churn_prediction:
        os.environ['CHURN_PREDICTION_EXAMPLE'] = 'true'
        
        # If running with churn prediction but no config path specified,
        # default to the example config path
        if 'ORCHESTRATOR_CONFIG_PATH' not in os.environ and not args.with_loan_prediction:
            example_config_path = os.path.join(os.getcwd(), "examples/churn_prediction/config")
            os.environ['ORCHESTRATOR_CONFIG_PATH'] = example_config_path
            print(f"Using churn prediction config path: {example_config_path}")
    
    if args.with_generic_orchestrator:
        os.environ['GENERIC_ORCHESTRATOR_EXAMPLE'] = 'true'
        
        # The generic orchestrator uses configurations from the main config directory
    
    # Run the server
    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)
