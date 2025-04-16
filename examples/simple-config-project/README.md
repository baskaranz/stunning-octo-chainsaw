# Simple Orchestrator API Project

This is a simple example project that demonstrates how to use Orchestrator API Service as a library, with only configuration files.

## Project Structure

```
simple-config-project/
├── config/
│   ├── config.yaml            # Global application settings
│   ├── database.yaml          # Database connection settings
│   ├── domains/
│   │   ├── hello.yaml         # Simple hello world endpoint
│   │   └── weather.yaml       # Weather API endpoint
│   └── integrations/
│       └── api_sources.yaml   # External API integration
├── requirements.txt           # Only needs orchestrator-api-service
└── README.md
```

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
orchestrator-api run --config-path ./config
```

## Available Endpoints

After starting the service, you can access:

1. **Hello World Endpoint**:
   - URL: http://localhost:8000/orchestrator/hello/greet/world
   - Description: Simple greeting endpoint that returns a hello message

2. **Weather API Endpoint**:
   - URL: http://localhost:8000/orchestrator/weather/current/{city}
   - Description: Sample endpoint that demonstrates API integration
   - Note: This is a mock endpoint for demonstration purposes

## API Documentation

You can view the full API documentation at http://localhost:8000/docs when the service is running.