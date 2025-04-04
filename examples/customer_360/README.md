# Customer 360 Example

This example demonstrates the orchestrator's capability to combine data from multiple sources into a unified customer view.

## What This Example Demonstrates

- Querying multiple database tables in a single request
- Transforming and combining data through configuration
- Creating a comprehensive API response with various data types
- Orchestrating data from different domains (customer profiles, orders, features, predictions)

## Quick Start

The easiest way to run this example is to use the provided `run_example.py` script:

```bash
# From the project root
python examples/customer_360/run_example.py
```

This script will:
1. Set up the example database
2. Start the orchestrator API service
3. Run the example with a default customer ID
4. Gracefully stop the service when done

To run with a different customer ID:

```bash
python examples/customer_360/run_example.py --customer cust_67890
```

## Manual Setup Instructions

If you prefer to run the example manually, follow these steps:

### 1. Create the Example Database

```bash
# From the project root
python examples/customer_360/setup_database.py
```

This creates a SQLite database with sample customer data in the examples/customer_360 directory.

### 2. Configure the Orchestrator

You have two options:

#### Option A: Use the Example Configurations Directly

Start the orchestrator with the example configuration:

```bash
# From the project root
ORCHESTRATOR_CONFIG_PATH=./examples/customer_360/config python main.py
```

#### Option B: Copy Example Configurations

Copy the example configurations to the main configuration directory:

```bash
cp examples/customer_360/config/* config/
```

Then start the orchestrator normally:

```bash
python main.py
```

### 3. Run the Example

```bash
python examples/customer_360/get_customer_360.py cust_12345
```

### 4. Gracefully Stop the Service

Instead of using `pkill`, you can use the provided stop script:

```bash
python scripts/stop_service.py
```

For forceful termination if needed:

```bash
python scripts/stop_service.py --force
```

## Available Sample Customers

- `cust_12345` - John Doe
- `cust_67890` - Jane Smith
- `cust_24680` - Michael Johnson

## Example Architecture

The Customer 360 example demonstrates the following components working together:

1. **Customer 360 Controller**: Handles API requests for customer 360 views
2. **Request Processor**: Coordinates the data orchestration process
3. **Data Orchestrator**: Retrieves data from multiple data sources
4. **Database Client**: Executes SQL queries against the example database
5. **Response Assembler**: Combines data from multiple sources into a unified response

## Configuration-Driven Architecture

This example showcases the orchestrator's configuration-driven approach. The `customer_360.yaml` configuration file defines:

- What data sources to query (customer profile, features, credit score, orders, predictions)
- What operations to perform on each source
- How to map data from sources to the final response

This declarative approach allows for rapid changes to the data flow without modifying code, making the system highly flexible and maintainable.

## Learn More

For more information on the orchestrator architecture and capabilities, see the [main documentation](../../docs/architecture/).