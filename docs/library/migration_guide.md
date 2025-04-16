# Migration Guide: Standalone to Library

This guide will help you migrate from using Orchestrator API Service as a standalone service to using it as a Python library.

## Why Migrate?

Using Orchestrator API Service as a library offers several advantages:

- **Simplified Deployment**: Package your application and the orchestrator together
- **Configuration Control**: Manage configurations within your project
- **Custom Extensions**: Extend the service with your own code
- **Reduced Dependencies**: No need for a separate orchestrator service
- **Streamlined Development**: Use a single codebase for your entire project

## Migration Steps

Follow these steps to migrate from standalone to library usage:

### 1. Install the Library

First, install the Orchestrator API Service library:

```bash
pip install orchestrator-api-service
```

### 2. Create a New Project Structure

Use the CLI to initialize a new project structure:

```bash
orchestrator-api init my-new-project
```

Or manually create the structure:

```
my-new-project/
├── config/
│   ├── config.yaml
│   ├── database.yaml
│   ├── domains/
│   └── integrations/
├── README.md
└── requirements.txt
```

### 3. Copy Your Configurations

Copy your existing configuration files to the new project structure:

```bash
# Copy all configuration files
cp -r old-project/config/* my-new-project/config/
```

Make sure to adapt the configurations to the new structure if needed.

### 4. Update Database Connections

Update database connection strings in `database.yaml` to use relative paths or environment variables:

```yaml
# Before
database:
  sources:
    default:
      connection_string: "sqlite:///absolute/path/to/database.db"

# After
database:
  sources:
    default:
      connection_string: "sqlite:///data/database.db"
```

### 5. Create a Runner Script (Optional)

For more control, create a custom runner script:

```python
#!/usr/bin/env python3
# run.py

import os
from orchestrator_api_service.cli import run_server

def main():
    # Set environment variables
    os.environ["CONFIG_PATH"] = os.path.join(os.path.dirname(__file__), "config")
    
    # Run the server
    run_server(
        host="0.0.0.0",
        port=8000,
        reload=True,
        config_path=os.environ["CONFIG_PATH"]
    )

if __name__ == "__main__":
    main()
```

### 6. Update Requirements

Update your `requirements.txt` file to include the library:

```
orchestrator-api-service>=0.1.0
# Other dependencies...
```

### 7. Run the Service

Run the service using the CLI:

```bash
cd my-new-project
orchestrator-api run --config-path ./config
```

Or use your custom runner script:

```bash
python run.py
```

## Adapting Custom Code

If you've made custom extensions to the standalone service, you'll need to adapt them to work with the library.

### Custom Controllers

If you have custom controllers, you can integrate them by creating a proper Python package:

1. Create a package structure:

```
my-new-project/
├── my_package/
│   ├── __init__.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── custom_controller.py
│   └── routes.py
```

2. In `routes.py`, add your routes:

```python
from fastapi import APIRouter
from my_package.controllers.custom_controller import CustomController

router = APIRouter()
controller = CustomController()

@router.get("/api/custom/{item_id}")
async def get_item(item_id: str):
    return await controller.get_item(item_id)
```

3. Create a custom runner that includes your routes:

```python
#!/usr/bin/env python3
# run.py

import os
from orchestrator_api_service.app import create_app
import uvicorn
from my_package.routes import router

def main():
    # Set environment variables
    os.environ["CONFIG_PATH"] = os.path.join(os.path.dirname(__file__), "config")
    
    # Create the app
    app = create_app()
    
    # Include your custom routes
    app.include_router(router)
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
```

### Custom Data Sources

If you've implemented custom data sources, you can integrate them by extending the library's data orchestrator:

1. Create a custom data orchestrator:

```python
# my_package/custom_orchestrator.py
from orchestrator_api_service.app.orchestration.data_orchestrator import DataOrchestrator

class CustomDataOrchestrator(DataOrchestrator):
    async def _execute_custom_source(self, source_type, source_id, operation, params, domain):
        if source_type == "my_custom_source":
            # Custom implementation
            return {"result": "custom data"}
        
        # Fall back to parent implementation
        return await super()._execute_source_operation(source_type, source_id, operation, params, domain)
```

2. Use your custom orchestrator in your runner:

```python
# run.py
from my_package.custom_orchestrator import CustomDataOrchestrator
from fastapi import FastAPI, Depends
from orchestrator_api_service.app import create_app

# Create the app
app = create_app()

# Add custom dependency overrides
app.dependency_overrides[DataOrchestrator] = CustomDataOrchestrator
```

## Common Migration Issues

### 1. Path Issues

If you're seeing path-related errors, ensure you're using the correct paths in your configurations:

```python
import os

# Get the absolute path to your project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set the config path
CONFIG_PATH = os.path.join(BASE_DIR, "config")
os.environ["CONFIG_PATH"] = CONFIG_PATH
```

### 2. Import Errors

If you encounter import errors, make sure your custom code is properly packaged:

```bash
# Make your package installable
pip install -e .
```

### 3. Dependency Conflicts

If you have dependency conflicts, try creating a separate virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Next Steps

After migration, you can:

1. **Optimize your configurations** for the library model
2. **Add custom extensions** to enhance functionality
3. **Implement proper packaging** for your project
4. **Set up CI/CD** for your new project structure

For more information, see the [Library Documentation](README.md) and [Configuration Guide](configuration_guide.md).