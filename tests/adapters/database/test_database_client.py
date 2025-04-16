import pytest
import sqlite3
import os
import tempfile
from unittest.mock import MagicMock, patch
import sqlalchemy
from sqlalchemy.orm import Session

from app.adapters.database.database_client import DatabaseClient
from app.config.data_source_config_manager import DataSourceConfigManager
from app.common.errors.custom_exceptions import DatabaseError


class TestDatabaseClient:
    """Tests for the DatabaseClient class."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        # Create a test table with sample data
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
        CREATE TABLE customer_features (
            customer_id TEXT PRIMARY KEY,
            lifetime_value REAL,
            churn_risk REAL,
            segment TEXT,
            last_updated TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE credit_scores (
            customer_id TEXT PRIMARY KEY,
            score INTEGER,
            report_date TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT,
            order_date TEXT,
            amount REAL,
            status TEXT,
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
        
        # Insert test customer features
        cursor.executemany("""
        INSERT INTO customer_features (customer_id, lifetime_value, churn_risk, segment, last_updated)
        VALUES (?, ?, ?, ?, ?)
        """, [
            ("cust_1234567890", 1500.50, 0.25, "high_value", "2025-01-01T12:00:00"),
            ("cust_0987654321", 850.75, 0.15, "medium_value", "2025-01-02T14:30:00"),
        ])
        
        # Insert test credit scores
        cursor.executemany("""
        INSERT INTO credit_scores (customer_id, score, report_date)
        VALUES (?, ?, ?)
        """, [
            ("cust_1234567890", 750, "2025-01-01"),
            ("cust_0987654321", 680, "2025-01-02"),
        ])
        
        # Insert test orders
        cursor.executemany("""
        INSERT INTO orders (order_id, customer_id, order_date, amount, status)
        VALUES (?, ?, ?, ?, ?)
        """, [
            ("order_001", "cust_1234567890", "2025-01-05", 120.50, "completed"),
            ("order_002", "cust_1234567890", "2025-01-10", 85.99, "completed"),
            ("order_003", "cust_1234567890", "2025-01-15", 200.00, "processing"),
            ("order_004", "cust_0987654321", "2025-01-07", 150.25, "completed"),
            ("order_005", "cust_0987654321", "2025-01-12", 75.50, "processing"),
        ])
        
        conn.commit()
        conn.close()
        
        print(f"Created temporary database at {path}")
        
        yield path
        
        # Clean up
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def config_manager(self, temp_db_path):
        """Create a mock config manager with test database configuration."""
        mock = MagicMock(spec=DataSourceConfigManager)
        
        db_path = f"sqlite:///{temp_db_path}"
        mock.get_data_source_config.return_value = {
            "connection_string": db_path,
            "connect_args": {"check_same_thread": False}
        }
        
        return mock
    
    @pytest.fixture
    def database_client(self, config_manager):
        """Create a database client with the test configuration."""
        with patch.object(DatabaseClient, '__init__', lambda self, config_manager: None):
            client = DatabaseClient(config_manager)
            client.config_manager = config_manager
            client.engines = {}
            client.sessions = {}
            return client
    
    @pytest.mark.asyncio
    async def test_get_engine(self, database_client, config_manager, temp_db_path):
        """Test getting a database engine."""
        # Call the method
        engine = database_client._get_engine("test_source")
        
        # Verify the engine was created
        assert engine is not None
        assert isinstance(engine, sqlalchemy.engine.Engine)
        assert engine.url.database == temp_db_path
        
        # Verify it's stored in the client's engines dictionary
        assert "test_source" in database_client.engines
        assert database_client.engines["test_source"] == engine
        
        # Verify config manager was called
        config_manager.get_data_source_config.assert_called_with("database", "test_source")
    
    @pytest.mark.asyncio
    async def test_get_engine_error(self, database_client, config_manager):
        """Test error handling when getting an engine."""
        # Setup mock to return None
        config_manager.get_data_source_config.return_value = None
        
        # Verify exception is raised
        with pytest.raises(DatabaseError, match="Database configuration not found"):
            database_client._get_engine("invalid_source")
    
    @pytest.mark.asyncio
    async def test_get_session(self, database_client):
        """Test getting a database session."""
        # First get an engine (test_get_engine verified this works)
        engine = database_client._get_engine("test_source")
        
        # Call the method
        session = database_client._get_session("test_source")
        
        # Verify the session was created
        assert session is not None
        assert isinstance(session, Session)
        
        # Verify the session factory is stored
        assert "test_source" in database_client.sessions
        
        # Get another session and verify it works
        another_session = database_client._get_session("test_source")
        assert another_session is not None
        assert isinstance(another_session, Session)
    
    @pytest.mark.asyncio
    async def test_query(self, database_client, temp_db_path):
        """Test executing a query."""
        # Get a real engine and session
        _ = database_client._get_engine("test_source")
        _ = database_client._get_session("test_source")
        
        # Execute a query
        query = "SELECT * FROM customers WHERE customer_id = :customer_id"
        params = {"customer_id": "cust_1234567890"}
        
        result = await database_client.query(query, params, "test_source")
        
        # Verify the result
        assert result is not None
        assert len(result) == 1
        assert result[0]["customer_id"] == "cust_1234567890"
        assert result[0]["name"] == "John Doe"
        assert result[0]["email"] == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_query_no_results(self, database_client):
        """Test query with no results."""
        # Get a real engine and session
        _ = database_client._get_engine("test_source")
        _ = database_client._get_session("test_source")
        
        # Execute a query for a non-existent customer
        query = "SELECT * FROM customers WHERE customer_id = :customer_id"
        params = {"customer_id": "non_existent_id"}
        
        result = await database_client.query(query, params, "test_source")
        
        # Verify empty result
        assert result is not None
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_query_error(self, database_client):
        """Test error handling in query execution."""
        # Get a real engine and session
        _ = database_client._get_engine("test_source")
        _ = database_client._get_session("test_source")
        
        # Execute a query with a syntax error
        invalid_query = "SELECT * FROMM customers"  # Intentional syntax error
        
        # Verify exception is raised
        with pytest.raises(DatabaseError, match="Error executing query"):
            await database_client.query(invalid_query, {}, "test_source")