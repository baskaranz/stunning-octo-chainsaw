import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sqlite3
import os
import tempfile
import asyncio

from app.adapters.feast.feast_client import FeastClient
from app.adapters.database.database_client import DatabaseClient
from app.config.data_source_config_manager import DataSourceConfigManager
from app.common.errors.custom_exceptions import FeastError, DatabaseError


class TestFeastDatabaseFallback:
    """Tests for the Feast database fallback mechanism with a real SQLite database."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        # Create a test table with sample data
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Create iris flowers table
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
        
        # Insert test data
        cursor.execute("""
        INSERT INTO iris_flowers (id, sepal_length, sepal_width, petal_length, petal_width, species)
        VALUES (1, 5.1, 3.5, 1.4, 0.2, 'setosa'),
               (2, 6.2, 2.9, 4.3, 1.3, 'versicolor'),
               (3, 7.9, 3.8, 6.4, 2.0, 'virginica')
        """)
        
        conn.commit()
        conn.close()
        
        print(f"Created temporary database at {path}")
        
        yield path
        
        # Clean up
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def config_manager(self, temp_db_path):
        """Create a mock config manager with database fallback configuration."""
        mock = MagicMock(spec=DataSourceConfigManager)
        
        db_path = f"sqlite:///{temp_db_path}"
        mock.get_data_source_config.side_effect = lambda type_name, source_id=None, domain=None: {
            "connection_string": db_path,
            "connect_args": {"check_same_thread": False}
        } if type_name == "database" else {
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
        
        return mock
    
    @pytest.fixture
    def database_client(self, temp_db_path):
        """Create a real database client with the temporary database."""
        # Create a test database engine directly
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker, Session
        import sqlalchemy
        import sqlite3
        
        # Create a subclass of DatabaseClient to override the query method for testing
        class TestDatabaseClient(DatabaseClient):
            async def query(self, query: str, params=None, source_id="default"):
                """Test version that handles SQLite parameter binding differently."""
                params = params or {}
                
                try:
                    # For SQLite IN clause with lists, we need special handling
                    if 'id' in params and isinstance(params['id'], list):
                        # Convert list to tuple for SQLite
                        id_list = params['id']
                        
                        # Replace IN (?) with IN (?, ?, ?) and provide values
                        # Count how many placeholders we need
                        placeholder_count = len(id_list)
                        placeholders = ', '.join(['?'] * placeholder_count)
                        modified_query = query.replace('IN (?)', f'IN ({placeholders})')
                        
                        # Execute raw SQL instead of using SQLAlchemy text
                        # Create connection directly to the temp database
                        conn = sqlite3.connect(temp_db_path)
                        cursor = conn.cursor()
                        cursor.execute(modified_query, id_list)
                        
                        # Process results
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                        conn.close()
                        return rows
                    else:
                        # For regular queries, use the session directly
                        # We access the session directly since we override _get_session
                        session = self.sessions["default"]
                        result = session.execute(sqlalchemy.text(query), params)
                        columns = result.keys()
                        rows = [dict(zip(columns, row)) for row in result.fetchall()]
                        session.commit()
                        return rows
                except Exception as e:
                    if "default" in self.sessions:
                        self.sessions["default"].rollback()
                    raise DatabaseError(f"Error executing query: {str(e)}", source_id)
                    
            # Override _get_session to avoid the 'Session is not callable' error
            def _get_session(self, source_id: str = "default"):
                """Get a database session for the specified source ID."""
                return self.sessions["default"]
        
        # Create a mock config manager
        config_manager = MagicMock(spec=DataSourceConfigManager)
        
        # Create our test database client with custom query method
        db_client = TestDatabaseClient(config_manager)
        
        # Set up a session that uses our temp database
        engine = create_engine(f"sqlite:///{temp_db_path}")
        Session = sessionmaker(bind=engine)
        db_client.sessions = {"default": Session()}
        
        return db_client
    
    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_database_fallback_with_real_database(
        self, mock_import, config_manager, database_client
    ):
        """Test Feast database fallback with a real database."""
        # Set up a mock for the feast module that will raise an import error
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create a client with the real database client
        client = FeastClient(config_manager, database_client)
        
        # Verify client is properly set up for fallback
        assert client.feast is None
        assert client.database_client is not None
        
        # Call get_online_features with entities that exist in the database
        entity_rows = [{"id": 1}, {"id": 2}, {"id": 3}]
        feature_refs = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
        
        result = await client.get_online_features(
            entity_rows=entity_rows,
            feature_refs=feature_refs,
            source_id="test",
            domain="test",
            use_fallback=True
        )
        
        # Verify results contain the expected features from database
        assert "iris:sepal_length" in result
        assert "iris:sepal_width" in result
        assert "iris:petal_length" in result
        assert "iris:petal_width" in result
        
        # Verify values match what's in the database
        assert result["iris:sepal_length"][0] == 5.1  # First entity
        assert result["iris:sepal_length"][1] == 6.2  # Second entity
        assert result["iris:sepal_length"][2] == 7.9  # Third entity
        
        # Test with an entity that doesn't exist
        entity_rows = [{"id": 999}]
        result = await client.get_online_features(
            entity_rows=entity_rows,
            feature_refs=feature_refs,
            source_id="test",
            domain="test",
            use_fallback=True
        )
        
        # Verify that we get None for nonexistent entities
        assert result["iris:sepal_length"][0] is None
    
    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_iris_features_with_real_database(
        self, mock_import, config_manager, database_client
    ):
        """Test get_iris_features with database fallback on a real database."""
        # Set up a mock for the feast module that will raise an import error
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create a client with the real database client
        client = FeastClient(config_manager, database_client)
        
        # Call get_iris_features for an entity that exists
        result = await client.get_iris_features(
            flower_id=2,
            source_id="test",
            domain="test"
        )
        
        # Verify results match database values for entity ID 2
        assert result["iris:sepal_length"] == 6.2
        assert result["iris:sepal_width"] == 2.9
        assert result["iris:petal_length"] == 4.3
        assert result["iris:petal_width"] == 1.3
        
        # Test with a custom subset of features
        custom_features = ["iris:sepal_length", "iris:sepal_width"]
        result = await client.get_iris_features(
            flower_id=3,
            feature_refs=custom_features,
            source_id="test",
            domain="test"
        )
        
        # Verify only requested features are returned
        assert "iris:sepal_length" in result
        assert "iris:sepal_width" in result
        assert "iris:petal_length" not in result
        assert "iris:petal_width" not in result
        
        # Verify values
        assert result["iris:sepal_length"] == 7.9
        assert result["iris:sepal_width"] == 3.8
    
    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_fallback_disabled(
        self, mock_import, config_manager, database_client
    ):
        """Test behavior when fallback is disabled."""
        # Set up a mock for the feast module that will raise an import error
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create a client with the real database client
        client = FeastClient(config_manager, database_client)
        
        # Modify the config to disable fallback
        modified_config = config_manager.get_data_source_config.return_value.copy()
        modified_config["database_fallback"]["enabled"] = False
        
        # Update the mock to return our modified config for feast type, but leave database config unchanged
        config_manager.get_data_source_config.side_effect = lambda type_name, source_id=None, domain=None: {
            "connection_string": f"sqlite:///{self.temp_db_path.name}",
            "connect_args": {"check_same_thread": False}
        } if type_name == "database" else modified_config
        
        # Verify that we get the correct error message when fallback is disabled
        with pytest.raises(FeastError, match="Feast module not available"):
            await client.get_online_features(
                entity_rows=[{"id": 1}],
                feature_refs=["iris:sepal_length"],
                source_id="test",
                domain="test",
                use_fallback=False  # Set this to False to avoid even checking the database fallback settings
            )
    
    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_concurrent_fallback_requests(
        self, mock_import, config_manager, database_client
    ):
        """Test concurrent fallback requests to ensure thread safety."""
        # Set up a mock for the feast module that will raise an import error
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create a client with the real database client
        client = FeastClient(config_manager, database_client)
        
        # Create a list of concurrent tasks
        tasks = []
        for i in range(5):  # 5 concurrent requests
            entity_rows = [{"id": id_val} for id_val in range(1, 4)]  # IDs 1-3
            feature_refs = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
            
            task = client.get_online_features(
                entity_rows=entity_rows,
                feature_refs=feature_refs,
                source_id="test",
                domain="test",
                use_fallback=True
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all results are correct
        for result in results:
            assert "iris:sepal_length" in result
            assert len(result["iris:sepal_length"]) == 3
            assert result["iris:sepal_length"][0] == 5.1
            assert result["iris:sepal_length"][1] == 6.2
            assert result["iris:sepal_length"][2] == 7.9