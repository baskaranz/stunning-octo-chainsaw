# Orchestrator API Service Library Documentation

This directory contains detailed documentation for using Orchestrator API Service as a Python library.

## Table of Contents

1. [Getting Started](getting_started.md) - Quick start guide for using the library
2. [Configuration Guide](configuration_guide.md) - Detailed explanation of configuration options
3. [CLI Reference](cli_reference.md) - Command-line interface reference
4. [Project Structure](project_structure.md) - Recommended project structure
5. [API Reference](api_reference.md) - Library API reference
6. [Migration Guide](migration_guide.md) - Migrating from standalone to library usage

## Overview

The Orchestrator API Service can be used in two ways:

1. **As a Python Library** (recommended) - Import and use in your own projects
2. **As a Standalone Service** - Run as a separate service

Using it as a library provides several advantages:
- Simplified deployment and configuration
- Better integration with your existing Python workflows
- Reduced infrastructure requirements

## Key Library Features

- **Command Line Interface (CLI)** - Initialize and run projects
- **Project Templates** - Quickly create new projects with templates
- **Configuration-Only Development** - Create projects with just YAML configurations
- **Flexible Integration** - Use with any Python application

## Quick Start

```bash
# Install the package
pip install orchestrator-api-service

# Create a new project
orchestrator-api init my-project

# Run the service
cd my-project
orchestrator-api run --config-path ./config
```

See the [Getting Started](getting_started.md) guide for more details.