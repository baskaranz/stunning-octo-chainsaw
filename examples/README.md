# Examples

This directory contains example implementations that demonstrate the capabilities of the Orchestrator API Service.

## Available Examples

### Customer 360 Example

The Customer 360 example demonstrates combining data from multiple sources into a unified customer view. It's located in the `customer_360/` directory.

#### Method 1: All-in-One Script

```bash
# Navigate to the project root directory
cd /path/to/orchestrator-api-service

# Run the all-in-one script
python examples/customer_360/run_example.py

# Or specify a different customer and port
python examples/customer_360/run_example.py --customer cust_67890 --port 8001
```

This script:
- Sets up the database with sample data
- Starts the orchestrator API service
- Runs the example client to fetch and display customer data
- Gracefully stops the service when done

#### Method 2: Step-by-Step with Python Client

```bash
# Navigate to the project root directory
cd /path/to/orchestrator-api-service

# Step 1: Create the database with sample data
python examples/customer_360/setup_database.py

# Step 2: Start the orchestrator API service with example config
ORCHESTRATOR_CONFIG_PATH=./examples/customer_360/config python main.py

# Step 3: In a new terminal, run the get_customer_360 script
python examples/customer_360/get_customer_360.py cust_12345

# Step 4: Gracefully stop the service when done
python scripts/stop_service.py
```

#### Method 3: Step-by-Step with curl

```bash
# Navigate to the project root directory
cd /path/to/orchestrator-api-service

# Step 1: Create the database with sample data
python examples/customer_360/setup_database.py

# Step 2: Start the orchestrator API service with example config
ORCHESTRATOR_CONFIG_PATH=./examples/customer_360/config python main.py

# Step 3: Use curl to query the API (in a new terminal)
curl -X GET "http://localhost:8000/api/customer-360/cust_12345" | json_pp

# Try other customers
curl -X GET "http://localhost:8000/api/customer-360/cust_67890" | json_pp

# Step 4: Gracefully stop the service when done
python scripts/stop_service.py
```

See the [Customer 360 Example README](customer_360/README.md) for more detailed information about this specific example.

## Example Structure Guidelines

Each example follows a standardized structure:

1. `README.md` - Detailed documentation specific to that example
2. `config/` - Configuration files required by the example
3. `run_example.py` - Script that runs the full example flow
4. Additional files specific to the example (setup scripts, sample clients, etc.)

Examples are designed to be self-contained and demonstrate specific capabilities of the Orchestrator API Service.