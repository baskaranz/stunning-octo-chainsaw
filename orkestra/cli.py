#!/usr/bin/env python3
"""
Command line interface for Orkestra
"""
import os
import sys
import argparse
import uvicorn
import logging
from typing import Optional, List
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('orkestra_cli')

def run_server(host: str = "0.0.0.0", 
              port: int = 8000, 
              reload: bool = False, 
              config_path: Optional[str] = None,
              log_level: str = "info") -> None:
    """
    Run the orchestrator API server
    
    Args:
        host: Host to bind the server to
        port: Port to run the server on
        reload: Whether to enable auto-reload
        config_path: Path to config directory
        log_level: Logging level
    """
    if config_path:
        os.environ["CONFIG_PATH"] = config_path
        logger.info(f"Using config path: {config_path}")
    
    # Check if the app module exists
    spec = importlib.util.find_spec("app")
    if spec is None:
        # If not, prefer using the library app module
        from orkestra.app import create_app
        
        # Create the app
        app = create_app()
        
        # Run the app using uvicorn
        uvicorn.run(
            "orkestra.app:app", 
            host=host, 
            port=port, 
            reload=reload,
            log_level=log_level.lower()
        )
    else:
        # Use the local app module if it exists
        try:
            from app import create_app
            
            # Create the app
            app = create_app()
            
            # Run using the local app module
            logger.info("Using local app module")
            uvicorn.run(
                "app:create_app", 
                host=host, 
                port=port, 
                reload=reload,
                log_level=log_level.lower(),
                factory=True
            )
        except ImportError:
            logger.error("Failed to import local app module. Falling back to library module.")
            from orkestra.app import create_app
            
            # Create the app
            app = create_app()
            
            # Run the app using uvicorn
            uvicorn.run(
                "orkestra.app:app", 
                host=host, 
                port=port, 
                reload=reload,
                log_level=log_level.lower()
            )

def init_project(project_dir: str) -> None:
    """
    Initialize a new project with the required directory structure
    
    Args:
        project_dir: Directory to create the project in
    """
    import shutil
    from pathlib import Path
    
    if os.path.exists(project_dir):
        if not os.path.isdir(project_dir):
            logger.error(f"{project_dir} exists but is not a directory")
            sys.exit(1)
    else:
        os.makedirs(project_dir)
    
    # Create necessary directories
    os.makedirs(os.path.join(project_dir, "config"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "config", "domains"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "config", "integrations"), exist_ok=True)
    
    # Get the template directory
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    
    # Copy template files
    shutil.copy(
        os.path.join(template_dir, "config.yaml"),
        os.path.join(project_dir, "config", "config.yaml")
    )
    
    shutil.copy(
        os.path.join(template_dir, "database.yaml"),
        os.path.join(project_dir, "config", "database.yaml")
    )
    
    # Create a simple README file
    with open(os.path.join(project_dir, "README.md"), "w") as f:
        f.write("""# Orkestra Project

This project was created with Orkestra.

## Running the service

```bash
# Start the service
orkestra --config-path ./config

# For development with auto-reload
orkestra --config-path ./config --reload
```

## Configuration

Configure your endpoints in the `config/domains/` directory.
""")
    
    # Create a simple example domain
    example_domain_dir = os.path.join(project_dir, "config", "domains", "example")
    os.makedirs(example_domain_dir, exist_ok=True)
    os.makedirs(os.path.join(example_domain_dir, "integrations"), exist_ok=True)
    
    # Copy example domain files
    shutil.copy(
        os.path.join(template_dir, "domains", "example.yaml"),
        os.path.join(project_dir, "config", "domains", "example.yaml")
    )
    
    logger.info(f"Project initialized at {project_dir}")
    logger.info("You can start the service by running:")
    logger.info(f"orkestra --config-path {project_dir}/config")

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description="Orkestra - Configurable API Service")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the Orkestra API server")
    run_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    run_parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    run_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    run_parser.add_argument("--config-path", type=str, help="Path to config directory")
    run_parser.add_argument("--log-level", type=str, default="info", 
                          choices=["debug", "info", "warning", "error", "critical"],
                          help="Logging level")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument("project_dir", type=str, help="Directory to create the project in")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Default to 'run' if no command is specified
    if args.command is None:
        # Handle direct usage without subcommand
        args.command = "run"
        args.host = "0.0.0.0"
        args.port = 8000
        args.reload = False
        args.config_path = None
        args.log_level = "info"
        
        # Check for legacy argument style
        for arg in sys.argv[1:]:
            if arg == "--reload":
                args.reload = True
            elif arg.startswith("--port="):
                args.port = int(arg.split("=")[1])
            elif arg.startswith("--host="):
                args.host = arg.split("=")[1]
            elif arg.startswith("--config-path=") or arg.startswith("--config="):
                args.config_path = arg.split("=")[1]
    
    # Execute the command
    if args.command == "run":
        run_server(args.host, args.port, args.reload, args.config_path, args.log_level)
    elif args.command == "init":
        init_project(args.project_dir)
    elif args.command == "version":
        from orkestra import __version__
        print(f"Orkestra version {__version__}")

if __name__ == "__main__":
    main()