from fastapi import APIRouter, HTTPException
import sqlite3
from pathlib import Path
import httpx
import pickle
import random
from typing import Dict, Any, List
import numpy as np
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_iris_by_id(flower_id: int) -> Dict[str, Any]:
    """Get iris flower data from the database by ID."""
    db_path = 'example/iris_example/iris_example.db'
    db_file = Path(db_path)
    
    if not db_file.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Database file not found: {db_path}"
        )
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the flower data
        cursor.execute('SELECT * FROM iris_flowers WHERE id = ?', (flower_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise HTTPException(
                status_code=404, 
                detail=f"Flower with ID {flower_id} not found"
            )
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        flower_data = dict(zip(columns, row))
        conn.close()
        
        return flower_data
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def get_random_samples(count: int = 5) -> List[Dict[str, Any]]:
    """Get random iris flower samples from the database."""
    db_path = 'example/iris_example/iris_example.db'
    db_file = Path(db_path)
    
    if not db_file.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Database file not found: {db_path}"
        )
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total count of records
        cursor.execute('SELECT COUNT(*) FROM iris_flowers')
        total_count = cursor.fetchone()[0]
        
        # Get random samples
        random_ids = random.sample(
            range(1, total_count + 1), 
            min(count, total_count)
        )
        
        samples = []
        for flower_id in random_ids:
            cursor.execute('SELECT * FROM iris_flowers WHERE id = ?', (flower_id,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                flower_data = dict(zip(columns, row))
                samples.append(flower_data)
        
        conn.close()
        return samples
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def predict_with_http_model(features: Dict[str, float]) -> Dict[str, Any]:
    """Make prediction using remote HTTP ML service."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "http://localhost:8502/predict",
                json={"features": features}
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    f"HTTP model returned status code {response.status_code}"
                )
                return None
    except Exception as e:
        logger.warning(f"HTTP model error: {str(e)}")
        return None


async def predict_with_local_model(features: Dict[str, float]) -> Dict[str, Any]:
    """Make prediction using locally saved model file."""
    model_path = Path('example/iris_example/models/iris_model.pkl')
    
    if not model_path.exists():
        logger.warning(f"Local model file not found: {model_path}")
        return None
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Convert features to numpy array in correct order
        feature_array = np.array([
            features['sepal_length'],
            features['sepal_width'],
            features['petal_length'],
            features['petal_width']
        ]).reshape(1, -1)
        
        # Get prediction
        class_index = model.predict(feature_array)[0]
        probabilities = model.predict_proba(feature_array)[0]
        
        # Map class indices to species names
        species_map = {0: 'setosa', 1: 'versicolor', 2: 'virginica'}
        predicted_class = species_map.get(class_index, f"unknown-{class_index}")
        
        # Create probability dictionary
        prob_dict = {
            species: float(prob) 
            for species, prob in zip(species_map.values(), probabilities)
        }
        
        return {
            "class_name": predicted_class,
            "probabilities": prob_dict
        }
    except Exception as e:
        logger.warning(f"Local model error: {str(e)}")
        return None


def rule_based_prediction(features: Dict[str, float]) -> Dict[str, Any]:
    """Make a rule-based prediction as fallback."""
    # Simple rule-based prediction based on Fisher's original paper
    if features['petal_length'] < 2.5:
        predicted_class = 'setosa'
        probabilities = {'setosa': 0.95, 'versicolor': 0.04, 'virginica': 0.01}
    elif features['petal_length'] < 4.9:
        predicted_class = 'versicolor'
        probabilities = {'setosa': 0.02, 'versicolor': 0.90, 'virginica': 0.08}
    else:
        predicted_class = 'virginica'
        probabilities = {'setosa': 0.01, 'versicolor': 0.15, 'virginica': 0.84}
    
    return {
        "class_name": predicted_class,
        "probabilities": probabilities
    }


@router.get("/{flower_id}")
async def get_iris_prediction(flower_id: int) -> Dict[str, Any]:
    """Get iris flower prediction by ID using a multi-tier approach."""
    try:
        # Step 1: Get flower data from database
        flower_data = await get_iris_by_id(flower_id)
        
        # Step 2: Extract features for prediction
        features = {
            'sepal_length': flower_data['sepal_length'],
            'sepal_width': flower_data['sepal_width'],
            'petal_length': flower_data['petal_length'],
            'petal_width': flower_data['petal_width']
        }
        
        # Step 3: Try to use HTTP model
        prediction = await predict_with_http_model(features)
        prediction_method = "http"
        
        # Step 4: If HTTP model fails, try local model
        if prediction is None:
            prediction = await predict_with_local_model(features)
            prediction_method = "local"
        
        # Step 5: If both methods fail, use rule-based approach
        if prediction is None:
            prediction = rule_based_prediction(features)
            prediction_method = "rule-based"
        
        # Step 6: Create the final response
        response = {
            'flower_id': flower_data['id'],
            'features': features,
            'actual_species': flower_data['species'],
            'prediction': prediction,
            'prediction_method': prediction_method
        }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in iris prediction: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting prediction: {str(e)}"
        )


@router.get("/samples/{count}")
async def get_samples(count: int = 5) -> List[Dict[str, Any]]:
    """Get multiple iris samples with predictions."""
    try:
        # Get random samples
        samples = await get_random_samples(count)
        
        # Add predictions to each sample
        result = []
        for flower in samples:
            features = {
                'sepal_length': flower['sepal_length'],
                'sepal_width': flower['sepal_width'],
                'petal_length': flower['petal_length'],
                'petal_width': flower['petal_width']
            }
            
            # Try each prediction method in order
            prediction = await predict_with_http_model(features)
            prediction_method = "http"
            
            if prediction is None:
                prediction = await predict_with_local_model(features)
                prediction_method = "local"
            
            if prediction is None:
                prediction = rule_based_prediction(features)
                prediction_method = "rule-based"
            
            result.append({
                'flower_id': flower['id'],
                'features': features,
                'actual_species': flower['species'],
                'prediction': prediction,
                'prediction_method': prediction_method
            })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in iris samples: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting samples: {str(e)}"
        )