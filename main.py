#!/usr/bin/env python3

import os
import argparse
import uvicorn
from app import create_app

# Create the base app
app = create_app()

# The generic orchestrator example uses a configuration-only approach
# so it doesn't need any code extensions

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Orchestrator API Service")
    parser.add_argument("--port", type=int, default=8000, help="Port number to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    
    args = parser.parse_args()
    
    # Run the server
    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)
