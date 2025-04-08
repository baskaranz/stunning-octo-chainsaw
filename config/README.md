# Core Configuration

This directory contains the core configuration templates for the Orchestrator API Service. These files provide the basic structure and examples for how to configure the service.

## Purpose

The configuration files in this directory are meant to serve as **templates** and **examples** of how to structure your own configuration. In a real deployment, you would:

1. Use these files as a starting point for your own configuration
2. Customize them for your specific use case
3. Deploy them in your application's config directory

## Configuration-Driven Development

The Orchestrator API Service follows a **configuration-driven development** approach where adding new endpoints or data sources requires minimal or no code changes, just configuration files. This approach provides several advantages:

- **Flexibility**: Easily adapt to different data source types and models
- **Modularity**: Configure each domain or use case independently
- **Maintainability**: Make changes without modifying core code

## Configuration File Structure

```
config/
├── config.yaml           # Global application settings
├── database.yaml         # Database connection templates
├── domains/              # Directory for domain-specific endpoint configurations
└── integrations/         # External system connection templates
    ├── api_sources.yaml  # External API connection templates
    └── feast_config.yaml # Feature store connection templates
```

## How to Use These Templates

When implementing the Orchestrator API Service in your application:

1. Copy these template files to your application's config directory
2. Modify them according to your requirements:
   - Update database connection strings
   - Configure API endpoints relevant to your services
   - Set up feature store connections
   - Create domain-specific endpoint definitions

## Example Configurations

For complete working examples of how to use these templates, see the [example/config](../example/config/) directory, which contains implementations for:

- Database-to-ML model scoring
- API-to-ML model scoring
- Feast-to-ML model scoring
- Multi-source model scoring

## Key Concepts

### Configuration References

The configurations use a reference system to connect different parts. For example:

1. Domain configurations reference data sources by `source_id`
2. Database operations use `params` that match placeholders in SQL queries
3. API operations use `path_params` that match placeholders in URL paths

### Configuration Inheritance

When you implement this service, you typically:

1. Start with these template configurations
2. Extend them with your own implementation details
3. Override specific settings as needed

## Getting Started

For detailed information on implementing and extending the Orchestrator API Service:

1. See the [project README.md](../README.md) for an overview
2. Check the [example configurations](../example/config/) for working examples
3. Review the [core service documentation](../docs/) for implementation details