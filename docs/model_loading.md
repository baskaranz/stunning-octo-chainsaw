# Model Loading Strategies

The Orchestrator API Service supports several strategies for loading and serving machine learning models:

1. **HTTP API Models**: Call an external model service over HTTP
2. **Local Artifact Models**: Load model artifacts from local filesystem and start a model server
3. **Docker Image Models**: Pull and run a model container from Docker
4. **ECR Models**: Pull and run a model container from Amazon ECR

## Configuration

Models can be configured in the ML configuration file for each domain. The configuration format supports multiple loading strategies through the `source` property.

### Base Configuration

All model configurations follow this basic structure:

```yaml
ml:
  sources:
    model_source_id:
      base_url: "http://fallback-url-if-loading-fails"
      models:
        model_id:
          endpoint: "/predict"
          # Optional: Model loading source configuration
          source:
            type: "local_artifact|docker|ecr"
            # Source-specific configuration
```

### HTTP API Model

This is the standard approach (without any dynamic loading):

```yaml
ml:
  sources:
    http_model:
      base_url: "http://localhost:5001"
      models:
        default:
          endpoint: "/predict"
          timeout: 30
          headers:
            Content-Type: "application/json"
```

### Local Artifact Model

Load a model from local files and start a model server:

```yaml
ml:
  sources:
    local_artifact_model:
      base_url: "http://localhost:5002"  # Fallback if loading fails
      models:
        default:
          endpoint: "/predict"
          source:
            type: "local_artifact"
            path: "./models/local_model"  # Path to model artifacts
            startup_command: "python -m app.serve --model_path ./model.pkl --port 8501"
            host: "localhost"
            port: 8501
            startup_delay: 5  # Seconds to wait for model to start
```

### Docker Image Model

Pull and run a model from Docker:

```yaml
ml:
  sources:
    docker_model:
      base_url: "http://localhost:5003"  # Fallback if loading fails
      models:
        default:
          endpoint: "/predict"
          source:
            type: "docker"
            image: "ml-model-service:latest"
            pull: true  # Set to false to use local image only
            host_port: 8502
            container_port: 8000
            environment:
              MODEL_PATH: "/app/models/model.pkl"
              LOG_LEVEL: "INFO"
            volumes:
              "./models": "/app/models"  # Host path: container path
            startup_delay: 8
```

### ECR Model

Pull and run a model from Amazon ECR:

```yaml
ml:
  sources:
    ecr_model:
      base_url: "http://localhost:5004"  # Fallback if loading fails
      models:
        default:
          endpoint: "/predict"
          source:
            type: "ecr"
            repository: "ml-models/prediction-service"
            tag: "latest"
            region: "us-east-1"
            host_port: 8503
            container_port: 8000
            environment:
              MODEL_TYPE: "production"
            startup_delay: 10
```

## Usage

Models are loaded on-demand when the first prediction request is made. Each model is cached, so subsequent requests use the same running model instance.

## API Endpoints

Models can be accessed through the standard domain endpoints:

```
POST /orchestrator/{domain_id}/{endpoint}
```

For example:

```
POST /orchestrator/model_loading_examples/local_artifact_model
{
  "feature1": 0.5,
  "feature2": 0.8
}
```

## Resource Management

Models are automatically shutdown when the application stops, ensuring proper resource cleanup. You can implement a custom endpoint to manually unload models if needed.

## Security Considerations

- **Local Artifact Models**: Ensure the startup command and model path are properly validated to prevent command injection.
- **Docker Models**: Use trusted images and consider running with restricted capabilities.
- **ECR Models**: Ensure proper IAM permissions for ECR access.