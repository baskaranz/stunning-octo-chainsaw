"""
Iris Database Setup and Utilities
"""
import os
import sqlite3
import pandas as pd
import numpy as np
from sklearn.datasets import load_iris
from typing import Dict, Any, List, Optional, Tuple

# Database file path
IRIS_DB_PATH = os.environ.get('IRIS_DB_PATH', 'iris_example.db')

def setup_database():
    """Create the database with sample iris data"""
    # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(IRIS_DB_PATH)
    cursor = conn.cursor()
    
    # Create the iris table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS iris_flowers (
        id INTEGER PRIMARY KEY,
        sepal_length REAL NOT NULL,
        sepal_width REAL NOT NULL,
        petal_length REAL NOT NULL,
        petal_width REAL NOT NULL,
        species TEXT,
        date_added TEXT
    )
    ''')
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM iris_flowers")
    count = cursor.fetchone()[0]
    
    # If table is empty, populate with iris dataset
    if count == 0:
        # Load the iris dataset
        iris = load_iris()
        iris_df = pd.DataFrame(data=np.c_[iris['data'], iris['target']],
                              columns=iris['feature_names'] + ['target'])
        
        # Rename columns to match our schema
        iris_df = iris_df.rename(columns={
            'sepal length (cm)': 'sepal_length',
            'sepal width (cm)': 'sepal_width',
            'petal length (cm)': 'petal_length',
            'petal width (cm)': 'petal_width'
        })
        
        # Map target numbers to species names
        target_map = {
            0: 'setosa',
            1: 'versicolor',
            2: 'virginica'
        }
        iris_df['species'] = iris_df['target'].map(target_map)
        
        # Add date_added column
        import datetime
        iris_df['date_added'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Drop the target column
        iris_df = iris_df.drop('target', axis=1)
        
        # Insert data into the database
        for _, row in iris_df.iterrows():
            cursor.execute('''
            INSERT INTO iris_flowers 
            (sepal_length, sepal_width, petal_length, petal_width, species, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                float(row['sepal_length']),
                float(row['sepal_width']),
                float(row['petal_length']),
                float(row['petal_width']),
                row['species'],
                row['date_added']
            ))
        
        print(f"Added {len(iris_df)} iris samples to the database")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database setup complete at {IRIS_DB_PATH}")

def get_iris_by_id(flower_id: int) -> Optional[Dict[str, Any]]:
    """Get a single iris flower by ID"""
    conn = sqlite3.connect(IRIS_DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM iris_flowers WHERE id = ?
    ''', (flower_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_iris_sample(count: int = 10) -> List[Dict[str, Any]]:
    """Get a sample of iris flowers"""
    conn = sqlite3.connect(IRIS_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(f'''
    SELECT * FROM iris_flowers ORDER BY RANDOM() LIMIT {count}
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_iris_counts() -> Dict[str, int]:
    """Get counts by species"""
    conn = sqlite3.connect(IRIS_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT species, COUNT(*) as count FROM iris_flowers GROUP BY species
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return {species: count for species, count in rows}

if __name__ == "__main__":
    # Setup the database when run directly
    setup_database()
    
    # Show a sample
    sample = get_iris_sample(5)
    print("\nSample of iris data:")
    for flower in sample:
        print(flower)
    
    # Show counts
    counts = get_iris_counts()
    print("\nCounts by species:")
    for species, count in counts.items():
        print(f"{species}: {count}")