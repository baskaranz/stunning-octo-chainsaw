"""
Isolated integration tests for DatabaseClient and FeastClient that don't depend on the full application.
This test bypasses the circular dependency issues in the main application code.
"""
import pytest
import sqlite3
import os
import tempfile
import asyncio
from unittest.mock import MagicMock, patch
import sqlalchemy

from app.adapters.database.database_client import DatabaseClient
from app.adapters.feast.feast_client import FeastClient
from app.common.errors.custom_exceptions import DatabaseError, FeastError


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path():
    """Create a temporary database file with test data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Create a test database with customers and features
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create test tables
    cursor.execute("""
    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        address TEXT,
        date_of_birth TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE iris_flowers (
        id INTEGER PRIMARY KEY,
        sepal_length REAL NOT NULL,
        sepal_width REAL NOT NULL,
        petal_length REAL NOT NULL,
        petal_width REAL NOT NULL,
        species TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE customer_features (
        customer_id TEXT PRIMARY KEY,
        lifetime_value REAL,
        churn_risk REAL,
        segment TEXT,
        last_updated TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    )
    """)
    
    # Insert test customers
    cursor.executemany("""
    INSERT INTO customers (customer_id, name, email, phone, address, date_of_birth, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ("cust_1234567890", "John Doe", "john@example.com", "555-1234", "123 Main St", "1980-01-01", "2025-01-01T12:00:00", "2025-01-01T12:00:00"),
        ("cust_0987654321", "Jane Smith", "jane@example.com", "555-5678", "456 Oak Ave", "1985-05-15", "2025-01-02T14:30:00", "2025-01-02T14:30:00"),
    ])
    
    # Insert test iris flowers
    cursor.executemany("""
    INSERT INTO iris_flowers (id, sepal_length, sepal_width, petal_length, petal_width, species)
    VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (1, 5.1, 3.5, 1.4, 0.2, "setosa"),
        (2, 6.2, 2.9, 4.3, 1.3, "versicolor"),
        (3, 7.9, 3.8, 6.4, 2.0, "virginica")
    ])
    
    # Insert test customer features
    cursor.executemany("""
    INSERT INTO customer_features (customer_id, lifetime_value, churn_risk, segment, last_updated)
    VALUES (?, ?, ?, ?, ?)
    """, [
        ("cust_1234567890", 1500.50, 0.25, "high_value", "2025-01-01T12:00:00"),
        ("cust_0987654321", 850.75, 0.15, "medium_value", "2025-01-02T14:30:00"),
    ])
    
    conn.commit()
    conn.close()
    
    print(f"Created temporary database at {path}")
    
    yield path
    
    # Clean up
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def config_manager(temp_db_path):
    """Create a mock config manager that works for both database and feast."""
    mock = MagicMock()
    
    db_path = f"sqlite:///{temp_db_path}"
    
    # Define the side effect function to handle different data source types
    def get_config_side_effect(data_source_type, source_id=None, domain=None):
        if data_source_type == "database":
            return {
                "connection_string": db_path,
                "connect_args": {"check_same_thread": False}
            }
        elif data_source_type == "feast":
            return {
                "repo_path": "./feature_repo/test",
                "project": "test",
                "default_iris_features": [
                    "iris:sepal_length", 
                    "iris:sepal_width", 
                    "iris:petal_length", 
                    "iris:petal_width"
                ],
                "database_fallback": {
                    "enabled": True,
                    "table": "iris_flowers",
                    "entity_key": "id",
                    "mapping": {
                        "iris:sepal_length": "sepal_length",
                        "iris:sepal_width": "sepal_width",
                        "iris:petal_length": "petal_length",
                        "iris:petal_width": "petal_width"
                    }
                }
            }
        return None
    
    # Set up the side effect
    mock.get_data_source_config.side_effect = get_config_side_effect
    
    return mock


@pytest.fixture
def database_client(config_manager, temp_db_path):
    """Create a database client with test configuration."""
    with patch.object(DatabaseClient, '__init__', lambda self, config_manager: None):
        client = DatabaseClient(config_manager)
        client.config_manager = config_manager
        client.engines = {}
        client.sessions = {}
        
        # Create a real engine for our temp database
        engine = sqlalchemy.create_engine(f"sqlite:///{temp_db_path}")
        client.engines["default"] = engine
        
        # Create a session factory
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        client.sessions["default"] = Session
        
        return client


@pytest.fixture
def feast_client(config_manager, database_client):
    """Create a feast client that will use database fallback."""
    # Create a patch for the feast module import to simulate it not being available
    with patch("app.adapters.feast.feast_client.importlib.import_module") as mock_import:
        # Set up the mock to raise ImportError
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create a feast client
        client = FeastClient(config_manager, database_client)
        
        return client


@pytest.mark.asyncio
async def test_get_customer_with_features(database_client, feast_client):
    """Test retrieving a customer and their features in a typical data pipeline."""
    # Step 1: Get customer data from the database
    customer = await database_client.get_customer("cust_1234567890")
    
    # Verify customer data was retrieved
    assert customer is not None
    assert customer["customer_id"] == "cust_1234567890"
    assert customer["name"] == "John Doe"
    
    # Step 2: Get customer features using the database client
    customer_features = await database_client.get_customer_features("cust_1234567890")
    
    # Verify customer features
    assert customer_features is not None
    assert customer_features["lifetime_value"] == 1500.50
    assert customer_features["churn_risk"] == 0.25
    assert customer_features["segment"] == "high_value"
    
    # Step 3: Create an enriched customer profile
    enriched_customer = {
        **customer,
        "features": customer_features
    }
    
    # Verify the enriched profile
    assert enriched_customer["customer_id"] == "cust_1234567890"
    assert enriched_customer["name"] == "John Doe"
    assert enriched_customer["features"]["lifetime_value"] == 1500.50


@pytest.mark.asyncio
async def test_feast_database_fallback_integration(database_client, feast_client):
    """Test the interaction between Feast client and database fallback."""
    # Get features for an iris flower through the feast client
    # This should use database fallback since feast is not available
    flower_features = await feast_client.get_iris_features(
        flower_id=2,
        source_id="test",
        domain="test"
    )
    
    # Verify features were retrieved from the database fallback
    assert flower_features is not None
    assert flower_features["iris:sepal_length"] == 6.2
    assert flower_features["iris:sepal_width"] == 2.9
    assert flower_features["iris:petal_length"] == 4.3
    assert flower_features["iris:petal_width"] == 1.3
    
    # Verify directly from database to confirm same values
    query = "SELECT * FROM iris_flowers WHERE id = :entity_id"
    result = await database_client.query(query, {"entity_id": 2})
    
    assert result[0]["sepal_length"] == 6.2
    assert result[0]["sepal_width"] == 2.9
    assert result[0]["petal_length"] == 4.3
    assert result[0]["petal_width"] == 1.3


@pytest.mark.asyncio
async def test_concurrent_data_fetching(database_client, feast_client):
    """Test concurrent data fetching from multiple sources."""
    # Create tasks for fetching data concurrently
    customer_task = database_client.get_customer("cust_1234567890")
    features_task = database_client.get_customer_features("cust_1234567890")
    iris_task = feast_client.get_iris_features(flower_id=1, source_id="test", domain="test")
    
    # Execute all tasks concurrently
    customer, features, iris_features = await asyncio.gather(
        customer_task, features_task, iris_task
    )
    
    # Verify all data was fetched correctly
    assert customer["name"] == "John Doe"
    assert features["lifetime_value"] == 1500.50
    assert iris_features["iris:sepal_length"] == 5.1
    
    # Create an enriched profile with all the data
    profile = {
        **customer,
        "customer_features": features,
        "iris_features": iris_features
    }
    
    # Verify the enriched profile
    assert profile["name"] == "John Doe"
    assert profile["customer_features"]["lifetime_value"] == 1500.50
    assert profile["iris_features"]["iris:sepal_length"] == 5.1