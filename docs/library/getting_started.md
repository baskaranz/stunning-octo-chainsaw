# Getting Started with Orkestra as a Library

This guide will help you get started using Orkestra as a Python library.

## Installation

Install the package from PyPI:

```bash
pip install orkestra
```

Or install from source:

```bash
git clone <repository-url>
cd orkestra
pip install -e .
```

## Creating a New Project

The easiest way to get started is to create a new project using the CLI:

```bash
# Create a new project
orkestra init my-orkestra-project

# Navigate to the project directory
cd my-orkestra-project
```

This will create a project with the following structure:

```
my-orkestra-project/
├── config/
│   ├── config.yaml            # Global application settings
│   ├── database.yaml          # Database connection settings
│   ├── domains/
│   │   └── example.yaml       # Example domain configuration
│   └── integrations/
└── README.md
```

## Running the Service

Once you've created your project, you can run the service using the CLI:

```bash
# Run the service using the config files
orkestra run --config-path ./config

# For development with auto-reload
orkestra run --reload --config-path ./config
```

By default, the service will start on http://localhost:8000.

## Creating Your First Endpoint

Let's create a simple "hello world" endpoint:

1. Create or edit the file `config/domains/hello.yaml`:

```yaml
# hello.yaml
domain_id: "hello"
description: "Simple hello world endpoints"

endpoints:
  greet:
    description: "A simple greeting endpoint"
    endpoint_type: "direct"
    method: "get"
    response_type: "json"
    
    # Direct response with no data sources
    response:
      message: "Hello, $request.path_params.name!"
      timestamp: "$system.timestamp"
```

2. Start the service:

```bash
orchestrator-api run --config-path ./config
```

3. Access your endpoint:

```bash
curl http://localhost:8000/orchestrator/hello/greet/world
```

Response:
```json
{
  "message": "Hello, world!",
  "timestamp": "2025-04-17T12:34:56.789Z"
}
```

## Using a Database

To connect to a database, configure your database connection in `config/database.yaml`:

```yaml
# database.yaml
database:
  sources:
    default:
      type: "sqlite"
      connection_string: "sqlite:///data/example.db"
      pool_size: 5
      max_overflow: 10
```

Then create a domain configuration that uses the database:

```yaml
# user.yaml
domain_id: "user"
description: "User management endpoints"

endpoints:
  get_user:
    description: "Get user by ID"
    endpoint_type: "composite"
    data_sources:
      - name: user_data
        type: database
        operation: get_user_by_id
        params:
          user_id: "$request.path_params.user_id"
    
    response_mapping:
      user_id: "$user_data.id"
      username: "$user_data.username"
      email: "$user_data.email"
```

## Next Steps

Now that you've created your first endpoints, you can:

1. Add more domains and endpoints
2. Configure database operations
3. Connect to external APIs
4. Set up ML model integration

For more detailed information, see the [Configuration Guide](configuration_guide.md).