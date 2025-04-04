import os
import pytest
from fastapi.testclient import TestClient
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app import create_app
from app.adapters.database.database_client import DatabaseClient
from app.config.data_source_config_manager import DataSourceConfigManager
from app.config.config_loader import ConfigLoader

# Test database URL (use in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def app_client():
    """Create a test client for the application."""
    app = create_app()
    
    with TestClient(app) as client:
        yield client

@pytest.fixture
def config_loader():
    """Create a config loader that uses test configurations."""
    # Use a test config directory if needed
    return ConfigLoader()

@pytest.fixture
def data_source_config(config_loader):
    """Create a data source config manager for testing."""
    return DataSourceConfigManager(config_loader)

@pytest.fixture
def test_db_engine():
    """Create a test database engine."""
    engine = sqlalchemy.create_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool  # Disable connection pooling for tests
    )
    
    # Create test tables
    metadata = sqlalchemy.MetaData()
    
    # Define test tables
    customers = sqlalchemy.Table(
        "customers",
        metadata,
        sqlalchemy.Column("customer_id", sqlalchemy.String, primary_key=True),
        sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
        sqlalchemy.Column("email", sqlalchemy.String, nullable=False),
        sqlalchemy.Column("phone", sqlalchemy.String),
        sqlalchemy.Column("address", sqlalchemy.String),
        sqlalchemy.Column("date_of_birth", sqlalchemy.Date),
        sqlalchemy.Column("created_at", sqlalchemy.DateTime, nullable=False),
        sqlalchemy.Column("updated_at", sqlalchemy.DateTime, nullable=False)
    )
    
    # Create all tables
    metadata.create_all(engine)
    
    yield engine
    
    # Drop all tables after tests
    metadata.drop_all(engine)

@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    
    yield session
    
    session.close()

@pytest.fixture
def database_client(test_db_engine, data_source_config):
    """Create a database client for testing."""
    client = DatabaseClient(data_source_config)
    
    # Override the engine with our test engine
    client.engines["default"] = test_db_engine
    
    # Override the session factory
    Session = sessionmaker(bind=test_db_engine)
    client.sessions["default"] = Session
    
    return client