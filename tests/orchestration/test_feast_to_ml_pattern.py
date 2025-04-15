import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import json

from app.orchestration.data_orchestrator import DataOrchestrator
from app.adapters.feast.feast_client import FeastClient
from app.adapters.database.database_client import DatabaseClient
from app.adapters.ml.model_client import ModelClient
from app.common.errors.custom_exceptions import FeastError


@pytest.fixture
def mock_database_client():
    """Mock database client that returns iris data."""
    mock = AsyncMock(spec=DatabaseClient)
    
    # Add mock data for iris flower
    mock.get_iris_by_id = AsyncMock(return_value={
        "id": 1,
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
        "species": "setosa"
    })
    
    return mock


@pytest.fixture
def mock_feast_client():
    """Mock feast client that returns feature data."""
    mock = AsyncMock(spec=FeastClient)
    
    # Add mock data for iris features
    mock.get_iris_features = AsyncMock(return_value={
        "iris:sepal_length": 6.2,
        "iris:sepal_width": 3.8,
        "iris:petal_length": 4.8,
        "iris:petal_width": 1.8
    })
    
    # Mock error case for testing fallback
    def mock_get_iris_features_error(*args, **kwargs):
        if kwargs.get("source_id") == "error_source":
            raise FeastError("Feast error", "error_source")
        return {
            "iris:sepal_length": 6.2,
            "iris:sepal_width": 3.8,
            "iris:petal_length": 4.8,
            "iris:petal_width": 1.8
        }
    
    mock.get_iris_features_with_error = AsyncMock(side_effect=mock_get_iris_features_error)
    
    return mock


@pytest.fixture
def mock_model_client():
    """Mock model client for predictions."""
    mock = AsyncMock(spec=ModelClient)
    
    # Add mock prediction
    mock.predict = AsyncMock(return_value={
        "prediction": {
            "class_name": "versicolor",
            "probabilities": {
                "setosa": 0.01,
                "versicolor": 0.95,
                "virginica": 0.04
            }
        }
    })
    
    return mock


@pytest.fixture
def mock_http_client():
    """Mock HTTP client."""
    return AsyncMock()


@pytest.fixture
def data_orchestrator(mock_database_client, mock_feast_client, mock_model_client, mock_http_client):
    """Create a DataOrchestrator with mock clients."""
    return DataOrchestrator(
        database=mock_database_client,
        http_client=mock_http_client,
        feast_client=mock_feast_client,
        model_client=mock_model_client
    )


class TestFeastToMLPattern:
    """Integration tests for the Feast -> ML pattern with database fallback."""
    
    @pytest.mark.asyncio
    async def test_feast_to_ml_pattern(self, data_orchestrator):
        """Test the Feast -> ML pattern flow."""
        # Setup endpoint configuration
        endpoint_config = {
            "domain_id": "iris_example",
            "endpoint_type": "composite",
            "data_sources": [
                # Get iris flower ID from request
                {
                    "name": "flower_id",
                    "type": "direct",
                    "params": {
                        "flower_id": 1
                    }
                },
                # Get iris features from Feast
                {
                    "name": "iris_features",
                    "type": "feast",
                    "source_id": "iris_features",
                    "operation": "get_iris_features",
                    "params": {
                        "flower_id": "$flower_id.flower_id"
                    }
                },
                # Get prediction from ML model using Feast features
                {
                    "name": "prediction",
                    "type": "ml",
                    "source_id": "http_model",
                    "operation": "predict",
                    "params": {
                        "features": {
                            "sepal_length": "$iris_features.iris:sepal_length",
                            "sepal_width": "$iris_features.iris:sepal_width",
                            "petal_length": "$iris_features.iris:petal_length",
                            "petal_width": "$iris_features.iris:petal_width"
                        }
                    }
                }
            ]
        }
        
        # Setup request data
        request_data = {
            "path_params": {
                "flower_id": 1
            }
        }
        
        # Execute the orchestration
        result = await data_orchestrator.orchestrate(
            execution_id="test-execution",
            endpoint_config=endpoint_config,
            request_data=request_data
        )
        
        # Verify Feast client was called
        data_orchestrator.sources["feast"].get_iris_features.assert_called_once_with(
            flower_id=1,
            source_id="iris_features",
            domain="iris_example"
        )
        
        # Verify ML model client was called with Feast features
        data_orchestrator.sources["ml"].predict.assert_called_once_with(
            model_id=ANY,
            features={
                "sepal_length": 6.2,
                "sepal_width": 3.8,
                "petal_length": 4.8,
                "petal_width": 1.8
            },
            source_id="http_model",
            domain="iris_example"
        )
        
        # Verify the final result structure
        assert "flower_id" in result
        assert "iris_features" in result
        assert "prediction" in result
        assert result["iris_features"]["iris:sepal_length"] == 6.2
        assert result["prediction"]["prediction"]["class_name"] == "versicolor"

    @pytest.mark.asyncio
    @patch("app.adapters.feast.feast_client.FeastClient.get_iris_features")
    async def test_feast_to_ml_pattern_with_fallback(self, mock_get_iris_features, data_orchestrator, mock_database_client):
        """Test the Feast -> ML pattern with database fallback."""
        # Make Feast client raise an error to trigger fallback
        mock_get_iris_features.side_effect = FeastError("Test error", "iris_features")
        
        # Setup database client to return fallback data
        # (in real code, the FeastClient would query the database)
        
        # Setup endpoint configuration
        endpoint_config = {
            "domain_id": "iris_example",
            "endpoint_type": "composite",
            "data_sources": [
                # Get iris flower ID from request
                {
                    "name": "flower_id",
                    "type": "direct",
                    "params": {
                        "flower_id": 1
                    }
                },
                # Get original data from database for comparison
                {
                    "name": "iris_data",
                    "type": "database",
                    "source_id": "default",
                    "operation": "get_iris_by_id",
                    "params": {
                        "flower_id": "$flower_id.flower_id"
                    }
                },
                # Get iris features from Feast (will fail and use fallback)
                {
                    "name": "iris_features",
                    "type": "feast",
                    "source_id": "iris_features",
                    "operation": "get_iris_features",
                    "params": {
                        "flower_id": "$flower_id.flower_id"
                    }
                },
                # Get prediction from ML model using features
                {
                    "name": "prediction",
                    "type": "ml",
                    "source_id": "http_model",
                    "operation": "predict",
                    "params": {
                        "features": {
                            "sepal_length": "$iris_features.iris:sepal_length || $iris_data.sepal_length",
                            "sepal_width": "$iris_features.iris:sepal_width || $iris_data.sepal_width",
                            "petal_length": "$iris_features.iris:petal_length || $iris_data.petal_length",
                            "petal_width": "$iris_features.iris:petal_width || $iris_data.petal_width"
                        }
                    }
                }
            ]
        }
        
        # Setup request data
        request_data = {
            "path_params": {
                "flower_id": 1
            }
        }
        
        # Execute the orchestration
        result = await data_orchestrator.orchestrate(
            execution_id="test-execution-fallback",
            endpoint_config=endpoint_config,
            request_data=request_data
        )
        
        # Verify database client was called for fallback
        data_orchestrator.sources["database"].get_iris_by_id.assert_called_once_with(
            flower_id=1,
            domain="iris_example"
        )
        
        # Verify the ML model was still called
        data_orchestrator.sources["ml"].predict.assert_called_once()
        
        # Verify the final result structure
        assert "flower_id" in result
        assert "iris_data" in result
        assert "prediction" in result
        
        # Check if fallback values from database were used
        # In a real environment, the Feast client would use the database fallback internally
        # This test simulates the case where the Feast client fails entirely
        assert result["iris_data"]["sepal_length"] == 5.1
        assert result["prediction"]["prediction"]["class_name"] == "versicolor"


@pytest.mark.asyncio
class TestEndToEndScenarios:
    """End-to-end scenarios for different patterns."""
    
    async def test_database_to_ml_pattern(self, data_orchestrator):
        """Test the traditional Database -> ML pattern."""
        # Setup endpoint configuration for Database -> ML pattern
        endpoint_config = {
            "domain_id": "iris_example",
            "endpoint_type": "composite",
            "data_sources": [
                # Get iris flower data from database
                {
                    "name": "iris_data",
                    "type": "database",
                    "source_id": "default",
                    "operation": "get_iris_by_id",
                    "params": {
                        "flower_id": 1
                    }
                },
                # Get prediction from ML model
                {
                    "name": "prediction",
                    "type": "ml",
                    "source_id": "http_model",
                    "operation": "predict",
                    "params": {
                        "features": {
                            "sepal_length": "$iris_data.sepal_length",
                            "sepal_width": "$iris_data.sepal_width",
                            "petal_length": "$iris_data.petal_length",
                            "petal_width": "$iris_data.petal_width"
                        }
                    }
                }
            ]
        }
        
        # Execute the orchestration
        result = await data_orchestrator.orchestrate(
            execution_id="test-database-ml",
            endpoint_config=endpoint_config,
            request_data={}
        )
        
        # Verify database client was called
        data_orchestrator.sources["database"].get_iris_by_id.assert_called_once_with(
            flower_id=1,
            domain="iris_example"
        )
        
        # Verify ML model client was called with database features
        data_orchestrator.sources["ml"].predict.assert_called_once_with(
            model_id=ANY,
            features={
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            },
            source_id="http_model",
            domain="iris_example"
        )
        
        # Verify the final result structure
        assert "iris_data" in result
        assert "prediction" in result
        assert result["iris_data"]["species"] == "setosa"
        assert result["prediction"]["prediction"]["class_name"] == "versicolor"
    
    async def test_compare_patterns(self, data_orchestrator):
        """Test comparing different patterns in one request."""
        # Setup endpoint configuration for comparison endpoint
        endpoint_config = {
            "domain_id": "iris_example",
            "endpoint_type": "composite",
            "data_sources": [
                # Get iris flower ID
                {
                    "name": "flower_id",
                    "type": "direct",
                    "params": {
                        "flower_id": 1
                    }
                },
                # Get iris data from database
                {
                    "name": "iris_data",
                    "type": "database",
                    "source_id": "default",
                    "operation": "get_iris_by_id",
                    "params": {
                        "flower_id": "$flower_id.flower_id"
                    }
                },
                # Get iris features from Feast
                {
                    "name": "iris_features",
                    "type": "feast",
                    "source_id": "iris_features",
                    "operation": "get_iris_features",
                    "params": {
                        "flower_id": "$flower_id.flower_id"
                    }
                },
                # Get prediction using database features
                {
                    "name": "db_prediction",
                    "type": "ml",
                    "source_id": "http_model",
                    "operation": "predict",
                    "params": {
                        "features": {
                            "sepal_length": "$iris_data.sepal_length",
                            "sepal_width": "$iris_data.sepal_width",
                            "petal_length": "$iris_data.petal_length",
                            "petal_width": "$iris_data.petal_width"
                        }
                    }
                },
                # Get prediction using Feast features
                {
                    "name": "feast_prediction",
                    "type": "ml",
                    "source_id": "http_model", 
                    "operation": "predict",
                    "params": {
                        "features": {
                            "sepal_length": "$iris_features.iris:sepal_length",
                            "sepal_width": "$iris_features.iris:sepal_width",
                            "petal_length": "$iris_features.iris:petal_length",
                            "petal_width": "$iris_features.iris:petal_width"
                        }
                    }
                }
            ]
        }
        
        # Execute the orchestration
        result = await data_orchestrator.orchestrate(
            execution_id="test-compare-patterns",
            endpoint_config=endpoint_config,
            request_data={}
        )
        
        # Verify all clients were called
        data_orchestrator.sources["database"].get_iris_by_id.assert_called_once()
        data_orchestrator.sources["feast"].get_iris_features.assert_called_once()
        
        # Verify ML model client was called twice (once for each pattern)
        assert data_orchestrator.sources["ml"].predict.call_count == 2
        
        # Verify the final result structure
        assert "flower_id" in result
        assert "iris_data" in result
        assert "iris_features" in result
        assert "db_prediction" in result
        assert "feast_prediction" in result
        
        # Check the values from each source
        assert result["iris_data"]["sepal_length"] == 5.1
        assert result["iris_features"]["iris:sepal_length"] == 6.2
        assert result["db_prediction"]["prediction"]["class_name"] == "versicolor"
        assert result["feast_prediction"]["prediction"]["class_name"] == "versicolor"