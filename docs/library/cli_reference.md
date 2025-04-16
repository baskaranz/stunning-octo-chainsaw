# CLI Reference

The Orchestrator API Service provides a command-line interface (CLI) for common operations. This document provides a reference for all available CLI commands.

## Command Overview

```bash
orchestrator-api [command] [options]
```

Available commands:

- `run`: Run the orchestrator API server
- `init`: Initialize a new project
- `version`: Show version information

If no command is specified, `run` is used as the default command.

## Run Command

The `run` command starts the orchestrator API server.

```bash
orchestrator-api run [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Host to bind the server to | `0.0.0.0` |
| `--port` | Port to run the server on | `8000` |
| `--reload` | Enable auto-reload for development | `False` |
| `--config-path` | Path to config directory | `None` |
| `--log-level` | Logging level (debug, info, warning, error, critical) | `info` |

### Examples

```bash
# Run with default settings
orchestrator-api run

# Run on a specific port
orchestrator-api run --port 8080

# Run with auto-reload for development
orchestrator-api run --reload

# Run with a custom config directory
orchestrator-api run --config-path ./my-config

# Run with debug logging
orchestrator-api run --log-level debug
```

## Init Command

The `init` command initializes a new project with the required directory structure and template files.

```bash
orchestrator-api init PROJECT_DIR
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PROJECT_DIR` | Directory to create the project in |

### Examples

```bash
# Create a new project in the current directory
orchestrator-api init my-project

# Create a new project with a specific path
orchestrator-api init /path/to/my-project
```

## Version Command

The `version` command displays the current version of the Orchestrator API Service.

```bash
orchestrator-api version
```

## Legacy Arguments

For backwards compatibility, the CLI also supports legacy argument style when no command is specified:

```bash
# Legacy style arguments
orchestrator-api --port=8080 --reload --config-path=./config
```

## Environment Variables

The CLI respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `CONFIG_PATH` | Path to config directory | `config` |
| `ORCHESTRATOR_CONFIG_PATH` | Alternative path to config directory | `None` |

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error |

## Programmatic Usage

You can also use the CLI functions in your Python code:

```python
from orchestrator_api_service.cli import run_server, init_project

# Run server
run_server(host="0.0.0.0", port=8000, reload=False, config_path="./config")

# Initialize a project
init_project("./my-new-project")
```