# Domain Configurations

This directory contains all the domain-specific configurations for the Orchestrator API Service. Each domain represents a logical group of related functionality that the orchestrator can process.

## Domain Organization

Each domain follows this organization:

```
domains/
├── domain_name.yaml              # Main domain configuration with endpoints
├── domain_name/                  # Domain-specific resources
│   ├── database.yaml             # Database configuration for this domain
│   └── integrations/             # Integration configurations
│       ├── api_sources.yaml      # API sources for this domain
│       ├── feast_config.yaml     # Feast feature store config for this domain
│       └── ml_config.yaml        # ML model configurations for this domain
```

## Available Domains

This directory is intended for your actual production domain configurations. For example configurations and demonstrations, please refer to the [example/config/domains](../../example/config/domains/) directory.

The following sample domain is available in the example directory:

### Sample Domain

- **Domain ID**: `sample_domain`
- **Description**: A sample domain configuration template to use as a starting point

### Example Domains (in example directory)

For complete working examples, see the [example/config/domains](../../example/config/domains/) directory, which includes:

- Iris flower classification example with database, Feast, and ML integration
- Various model scoring examples for different use cases
- Model loading examples demonstrating different deployment strategies

## Adding a New Domain

To add a new domain:

1. Create a domain configuration file: `domains/your_domain.yaml`
2. Create a domain directory: `domains/your_domain/`
3. Add domain-specific configurations:
   - `domains/your_domain/database.yaml`
   - `domains/your_domain/integrations/api_sources.yaml`
   - `domains/your_domain/integrations/ml_config.yaml`
   - etc.
4. Restart the orchestrator service or use the reload endpoint

The orchestrator will automatically discover and load all domain configurations from this directory.

> **Note**: Keep example configurations in the example directory to maintain a clean separation between actual system configurations and demonstration examples.