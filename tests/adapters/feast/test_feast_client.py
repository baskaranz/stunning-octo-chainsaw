import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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


class TestFeastClient:

    @patch("app.adapters.feast.feast_client.importlib.import_module")
    def test_init_with_feast_available(self, mock_import, mock_config_manager):
        # Setup mock
        mock_feast = MagicMock()
        mock_import.return_value = mock_feast
        
        # Create client
        client = FeastClient(mock_config_manager)
        
        # Check feast module was imported
        mock_import.assert_called_once_with("feast")
        assert client.feast == mock_feast
        assert client.feature_stores == {}

    @patch("app.adapters.feast.feast_client.importlib.import_module")
    def test_init_with_feast_unavailable(self, mock_import, mock_config_manager):
        # Setup mock to raise ImportError
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create client
        client = FeastClient(mock_config_manager)
        
        # Check feast is None
        assert client.feast is None

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_online_features_with_fallback(
        self, mock_import, mock_config_manager, mock_database_client
    ):
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
        assert "iris:sepal_length" in result
        assert result["iris:sepal_length"] == [5.1]

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_online_features_without_fallback(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        # Setup mock to raise ImportError
        mock_import.side_effect = ImportError("No module named 'feast'")
        
        # Create client with database client
        client = FeastClient(mock_config_manager, mock_database_client)
        
        # Call get_online_features without fallback
        entity_rows = [{"id": 1}]
        feature_refs = ["iris:sepal_length", "iris:sepal_width", "iris:petal_length", "iris:petal_width"]
        
        with pytest.raises(FeastError):
            await client.get_online_features(
                entity_rows=entity_rows,
                feature_refs=feature_refs,
                source_id="iris_features",
                domain="iris_example",
                use_fallback=False
            )

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.importlib.import_module")
    async def test_get_iris_features(
        self, mock_import, mock_config_manager, mock_database_client
    ):
        # Setup mock to raise ImportError
        mock_import.side_effect = ImportError("No module named 'feast'")
        
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
        client.get_online_features.assert_called_once()
        assert result["iris:sepal_length"] == 5.1
        assert result["iris:sepal_width"] == 3.5
        assert result["iris:petal_length"] == 1.4
        assert result["iris:petal_width"] == 0.2