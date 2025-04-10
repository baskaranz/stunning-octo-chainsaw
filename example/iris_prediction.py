from pathlib import Path
import sqlite3
import json
import sys

def get_iris_prediction(flower_id):
    # Get the flower data from the database
    db_path = 'example/iris_example.db'
    db_file = Path(db_path)
    
    if not db_file.exists():
        return {'error': f'Database file not found: {db_path}'}
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the flower data
        cursor.execute('SELECT * FROM iris_flowers WHERE id = ?', (flower_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {'error': f'Flower with ID {flower_id} not found'}
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        flower_data = dict(zip(columns, row))
        conn.close()
        
        # Extract features
        features = {
            'sepal_length': flower_data['sepal_length'],
            'sepal_width': flower_data['sepal_width'],
            'petal_length': flower_data['petal_length'],
            'petal_width': flower_data['petal_width']
        }
        
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
        
        # Create the response
        response = {
            'flower_id': flower_data['id'],
            'features': features,
            'actual_species': flower_data['species'],
            'prediction': {
                'class_name': predicted_class,
                'probabilities': probabilities
            }
        }
        
        return response
        
    except Exception as e:
        return {'error': f'Error getting prediction: {str(e)}'}

if __name__ == '__main__':
    flower_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    result = get_iris_prediction(flower_id)
    print(json.dumps(result, indent=2))