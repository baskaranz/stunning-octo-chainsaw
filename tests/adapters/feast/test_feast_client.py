import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import importlib
from typing import Dict, List, Any

from app.adapters.feast.feast_client import FeastClient
from app.common.errors.custom_exceptions import FeastError


@pytest.fixture
def mock_config_manager():
    mock = MagicMock()
    mock.get_data_source_config.return_value = {
        "repo_path": "./feature_repo/iris_example",
        "project": "iris_example",
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
def mock_database_client():
    mock = AsyncMock()
    mock.query.return_value = [
        {
            "id": 1,
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
            "species": "setosa"
        }
    ]
    return mock


@pytest.fixture
def mock_feast():
    mock_feast = MagicMock()
    mock_feature_store = MagicMock()
    mock_feature_store.get_online_features.return_value = MagicMock()
    
    # Setup feature values in the feast response
    feast_response = mock_feature_store.get_online_features.return_value
    feast_response.keys.return_value = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
    feast_response.__getitem__.side_effect = lambda key: [6.2] if key == "iris:sepal_length" else [3.8] if key == "iris:sepal_width" else [4.8] if key == "iris:petal_length" else [1.8]
    
    # Setup feature store connection
    mock_feast.FeatureStore.return_value = mock_feature_store
    
    return mock_feast


class TestFeastClient:
    """Tests for the FeastClient class."""

    @patch("app.adapters.feast.feast_client.importlib.import_module")
    def test_init_with_feast_available(self, mock_import, mock_config_manager):
        """Test initialization when Feast is available."""
        # Setup mock
        mock_feast = MagicMock()
        mock_import.return_value = mock_feast
        
        # Create client
        client = FeastClient(mock_config_manager)
        
        # Check feast module was imported
        mock_import.assert_called_once_with("feast")
        assert client.feast == mock_feast
        assert client.feature_stores == {}
        assert client.database_client is not None

    @patch("app.adapters.feast.feast_client.importlib.import_module")
    def test_init_with_feast_unavailable(self, mock_import, mock_config_manager):
        """Test initialization when Feast is unavailable."""
        # Setup mock to raise ImportError
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create client
        client = FeastClient(mock_config_manager)
        
        # Check feast is None
        assert client.feast is None
        assert client.database_client is not None

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_feature_store(self, mock_import, mock_config_manager, mock_feast):
        """Test _get_feature_store method."""
        # Setup mock
        mock_import.return_value = mock_feast
        
        # Create client
        client = FeastClient(mock_config_manager)
        
        # Call _get_feature_store
        feature_store = client._get_feature_store("iris_features")
        
        # Verify config is retrieved correctly
        mock_config_manager.get_data_source_config.assert_called_with("feast", "iris_features")
        
        # Verify feast feature store is created
        mock_feast.FeatureStore.assert_called_once_with(repo_path="./feature_repo/iris_example")
        
        # Verify feature store is stored and returned
        assert client.feature_stores["iris_features"] == feature_store
        
        # Call again to test caching
        client._get_feature_store("iris_features")
        
        # Verify feast feature store is only created once
        mock_feast.FeatureStore.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_feature_store_error(self, mock_import, mock_config_manager):
        """Test _get_feature_store with various error conditions."""
        # Setup mock
        mock_import.return_value = MagicMock()
        
        # Create client
        client = FeastClient(mock_config_manager)
        
        # Test with missing config
        mock_config_manager.get_data_source_config.return_value = None
        
        with pytest.raises(FeastError, match="Feast configuration not found for source 'missing'"):
            client._get_feature_store("missing")
        
        # Test with missing repo_path
        mock_config_manager.get_data_source_config.return_value = {}
        
        with pytest.raises(FeastError, match="Missing repo path for Feast source 'no_repo_path'"):
            client._get_feature_store("no_repo_path")
        
        # Test with exception in feature store creation
        mock_config_manager.get_data_source_config.return_value = {"repo_path": "invalid_path"}
        client.feast.FeatureStore.side_effect = Exception("Failed to initialize")
        
        with pytest.raises(FeastError, match="Error initializing Feast feature store: Failed to initialize"):
            client._get_feature_store("error_store")

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_online_features_with_feast(
        self, mock_import, mock_config_manager, mock_feast
    ):
        """Test get_online_features when Feast is available."""
        # Setup mock
        mock_import.return_value = mock_feast
        
        # Create client
        client = FeastClient(mock_config_manager)
        
        # Call get_online_features
        entity_rows = [{"id": 1}]
        feature_refs = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
        
        result = await client.get_online_features(
            entity_rows=entity_rows,
            feature_refs=feature_refs,
            source_id="iris_features"
        )
        
        # Verify feature store is retrieved
        mock_feast.FeatureStore.assert_called_once()
        
        # Verify get_online_features is called correctly
        feature_store = mock_feast.FeatureStore.return_value
        feature_store.get_online_features.assert_called_once_with(
            entity_rows=entity_rows,
            features=feature_refs
        )
        
        # Verify results are processed correctly
        assert "iris:sepal_length" in result
        assert result["iris:sepal_length"] == [6.2]
        assert result["iris:sepal_width"] == [3.8]
        assert result["iris:petal_length"] == [4.8]
        assert result["iris:petal_width"] == [1.8]

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_online_features_feast_error_with_fallback(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test get_online_features when Feast is available but fails, with fallback."""
        # Setup mock
        mock_feast = MagicMock()
        mock_feature_store = MagicMock()
        mock_feature_store.get_online_features.side_effect = Exception("Feast error")
        mock_feast.FeatureStore.return_value = mock_feature_store
        mock_import.return_value = mock_feast
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Call get_online_features with fallback
        entity_rows = [{"id": 1}]
        feature_refs = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
        
        result = await client.get_online_features(
            entity_rows=entity_rows,
            feature_refs=feature_refs,
            source_id="iris_features",
            domain="iris_example",
            use_fallback=True
        )
        
        # Verify feature store error and fallback
        mock_feature_store.get_online_features.assert_called_once()
        mock_database_client.query.assert_called_once()
        
        # Verify database fallback results
        assert "iris:sepal_length" in result
        assert result["iris:sepal_length"] == [5.1]
        assert result["iris:sepal_width"] == [3.5]
        assert result["iris:petal_length"] == [1.4]
        assert result["iris:petal_width"] == [0.2]

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_online_features_feast_error_without_fallback(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test get_online_features when Feast is available but fails, without fallback."""
        # Setup mock
        mock_feast = MagicMock()
        mock_feature_store = MagicMock()
        mock_feature_store.get_online_features.side_effect = Exception("Feast error")
        mock_feast.FeatureStore.return_value = mock_feature_store
        mock_import.return_value = mock_feast
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Call get_online_features without fallback
        entity_rows = [{"id": 1}]
        feature_refs = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
        
        with pytest.raises(FeastError, match="Failed to retrieve features: Feast error"):
            await client.get_online_features(
                entity_rows=entity_rows,
                feature_refs=feature_refs,
                source_id="iris_features",
                domain="iris_example",
                use_fallback=False
            )
        
        # Verify feature store error, but no fallback
        mock_feature_store.get_online_features.assert_called_once()
        mock_database_client.query.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_online_features_with_fallback_feast_unavailable(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test get_online_features when Feast is unavailable, with fallback."""
        # Setup mock to raise ImportError
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Call get_online_features with fallback
        entity_rows = [{"id": 1}]
        feature_refs = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
        
        result = await client.get_online_features(
            entity_rows=entity_rows,
            feature_refs=feature_refs,
            source_id="iris_features",
            domain="iris_example",
            use_fallback=True
        )
        
        # Check database fallback was used
        mock_database_client.query.assert_called_once()
        
        # Expected SQL query with proper column mapping
        expected_query = "SELECT id, sepal_length, sepal_width, petal_length, petal_width FROM iris_flowers WHERE id IN (?)"
        # Note: The exact SQL may vary by implementation, so we're verifying the key components rather than exact string
        assert "SELECT" in mock_database_client.query.call_args[0][0]
        assert "FROM iris_flowers" in mock_database_client.query.call_args[0][0]
        assert "WHERE id IN" in mock_database_client.query.call_args[0][0]
        
        # Verify results
        assert "iris:sepal_length" in result
        assert result["iris:sepal_length"] == [5.1]
        assert result["iris:sepal_width"] == [3.5]
        assert result["iris:petal_length"] == [1.4]
        assert result["iris:petal_width"] == [0.2]

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_online_features_without_fallback_feast_unavailable(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test get_online_features when Feast is unavailable, without fallback."""
        # Setup mock to raise ImportError
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Call get_online_features without fallback
        entity_rows = [{"id": 1}]
        feature_refs = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
        
        with pytest.raises(FeastError, match="Feast module not available"):
            await client.get_online_features(
                entity_rows=entity_rows,
                feature_refs=feature_refs,
                source_id="iris_features",
                domain="iris_example",
                use_fallback=False
            )
        
        # Check database fallback was not used
        mock_database_client.query.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_features_from_database(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test _get_features_from_database method."""
        # Setup mock
        mock_import.return_value = MagicMock()
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Call _get_features_from_database
        entity_rows = [{"id": 1}, {"id": 2}]
        feature_refs = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
        
        result = await client._get_features_from_database(
            entity_rows=entity_rows,
            feature_refs=feature_refs,
            source_id="iris_features",
            domain="iris_example"
        )
        
        # Verify database query
        mock_database_client.query.assert_called_once()
        
        # Verify feature mappings
        assert "iris:sepal_length" in result
        assert "iris:sepal_width" in result
        assert "iris:petal_length" in result
        assert "iris:petal_width" in result
        
        # For the entity we have a match in the database
        assert result["iris:sepal_length"][0] == 5.1
        
        # For the entity we don't have a match, we should get None values
        assert result["iris:sepal_length"][1] is None

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_features_from_database_error_conditions(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test _get_features_from_database with various error conditions."""
        # Setup mock
        mock_import.return_value = MagicMock()
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Test with no database client
        client.database_client = None
        
        with pytest.raises(FeastError, match="Database client not available for fallback"):
            await client._get_features_from_database(
                entity_rows=[{"id": 1}],
                feature_refs=["iris:sepal_length"],
                source_id="iris_features"
            )
        
        # Restore database client
        client.database_client = mock_database_client
        
        # Test with missing config
        mock_config_manager.get_data_source_config.return_value = None
        
        with pytest.raises(FeastError, match="Feast configuration not found for source 'missing_config'"):
            await client._get_features_from_database(
                entity_rows=[{"id": 1}],
                feature_refs=["iris:sepal_length"],
                source_id="missing_config"
            )
        
        # Test with fallback not enabled
        mock_config_manager.get_data_source_config.return_value = {
            "database_fallback": {"enabled": False}
        }
        
        with pytest.raises(FeastError, match="Database fallback not enabled for source 'fallback_disabled'"):
            await client._get_features_from_database(
                entity_rows=[{"id": 1}],
                feature_refs=["iris:sepal_length"],
                source_id="fallback_disabled"
            )
        
        # Test with incomplete fallback config
        mock_config_manager.get_data_source_config.return_value = {
            "database_fallback": {"enabled": True}
        }
        
        with pytest.raises(FeastError, match="Incomplete database fallback configuration for source 'incomplete_config'"):
            await client._get_features_from_database(
                entity_rows=[{"id": 1}],
                feature_refs=["iris:sepal_length"],
                source_id="incomplete_config"
            )
        
        # Test with no entity IDs matching entity_key
        mock_config_manager.get_data_source_config.return_value = {
            "database_fallback": {
                "enabled": True,
                "table": "iris_flowers",
                "entity_key": "unknown_key",
                "mapping": {"iris:sepal_length": "sepal_length"}
            }
        }
        
        with pytest.raises(FeastError, match="No entity IDs found in entity rows for key 'unknown_key'"):
            await client._get_features_from_database(
                entity_rows=[{"id": 1}],
                feature_refs=["iris:sepal_length"],
                source_id="missing_entity_key"
            )

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_iris_features(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test get_iris_features method."""
        # Setup mock
        mock_import.return_value = MagicMock()
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Patch the get_online_features method
        client.get_online_features = AsyncMock()
        client.get_online_features.return_value = {
            "iris:sepal_length": [5.1],
            "iris:sepal_width": [3.5],
            "iris:petal_length": [1.4],
            "iris:petal_width": [0.2]
        }
        
        # Call get_iris_features
        result = await client.get_iris_features(
            flower_id=1,
            source_id="iris_features",
            domain="iris_example"
        )
        
        # Check get_online_features was called correctly
        client.get_online_features.assert_called_once_with(
            entity_rows=[{"id": 1}],
            feature_refs=mock_config_manager.get_data_source_config.return_value["default_iris_features"],
            source_id="iris_features",
            domain="iris_example",
            use_fallback=True
        )
        
        # Verify results
        assert result["iris:sepal_length"] == 5.1
        assert result["iris:sepal_width"] == 3.5
        assert result["iris:petal_length"] == 1.4
        assert result["iris:petal_width"] == 0.2

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_iris_features_with_custom_features(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test get_iris_features with custom feature references."""
        # Setup mock
        mock_import.return_value = MagicMock()
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Patch the get_online_features method
        client.get_online_features = AsyncMock()
        client.get_online_features.return_value = {
            "iris:sepal_length": [5.1],
            "iris:sepal_width": [3.5]
        }
        
        # Call get_iris_features with custom feature refs
        custom_features = ["iris:sepal_length", "iris:sepal_width"]
        result = await client.get_iris_features(
            flower_id=1,
            feature_refs=custom_features,
            source_id="iris_features",
            domain="iris_example"
        )
        
        # Check get_online_features was called with custom features
        client.get_online_features.assert_called_once_with(
            entity_rows=[{"id": 1}],
            feature_refs=custom_features,
            source_id="iris_features",
            domain="iris_example",
            use_fallback=True
        )
        
        # Verify results include only requested features
        assert result["iris:sepal_length"] == 5.1
        assert result["iris:sepal_width"] == 3.5
        assert "iris:petal_length" not in result
        assert "iris:petal_width" not in result

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_iris_features_error_handling(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test error handling in get_iris_features."""
        # Setup mock
        mock_import.return_value = MagicMock()
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Patch the get_online_features method to raise error
        client.get_online_features = AsyncMock()
        client.get_online_features.side_effect = FeastError("Test error", "iris_features")
        
        # Call get_iris_features
        with pytest.raises(FeastError, match="Failed to retrieve iris features: Test error"):
            await client.get_iris_features(
                flower_id=1,
                source_id="iris_features",
                domain="iris_example"
            )
        
        # Verify get_online_features was called
        client.get_online_features.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_customer_features(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        """Test get_customer_features method."""
        # Setup mock
        mock_import.return_value = MagicMock()
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Patch the get_online_features method
        client.get_online_features = AsyncMock()
        client.get_online_features.return_value = {
            "customer:feature1": [100],
            "customer:feature2": ["value"],
            "customer:feature3": [True]
        }
        
        # Update config for customer features
        mock_config_manager.get_data_source_config.return_value["default_customer_features"] = [
            "customer:feature1", "customer:feature2", "customer:feature3"
        ]
        
        # Call get_customer_features
        result = await client.get_customer_features(
            customer_id="cust123",
            source_id="customer_features",
            domain="customer_domain"
        )
        
        # Check get_online_features was called correctly
        client.get_online_features.assert_called_once_with(
            entity_rows=[{"customer_id": "cust123"}],
            feature_refs=["customer:feature1", "customer:feature2", "customer:feature3"],
            source_id="customer_features",
            domain="customer_domain",
            use_fallback=True
        )
        
        # Verify results
        assert result["customer:feature1"] == 100
        assert result["customer:feature2"] == "value"
        assert result["customer:feature3"] is True