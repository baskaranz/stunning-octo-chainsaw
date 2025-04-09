"""
Iris Database Setup and Utilities
"""
import os
import sqlite3
import datetime
from typing import Dict, Any, List, Optional

# Database file path - using the same path specified in the config file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(SCRIPT_DIR, 'iris_example.db')
IRIS_DB_PATH = os.environ.get('IRIS_DB_PATH', DEFAULT_DB_PATH)

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
    
    # If table is empty, populate with hardcoded iris dataset (simplified subset)
    if count == 0:
        # Hardcoded sample of the iris dataset (3 samples of each species)
        iris_samples = [
            # setosa samples
            (5.1, 3.5, 1.4, 0.2, 'setosa'),
            (4.9, 3.0, 1.4, 0.2, 'setosa'),
            (4.7, 3.2, 1.3, 0.2, 'setosa'),
            
            # versicolor samples
            (6.4, 3.2, 4.5, 1.5, 'versicolor'),
            (6.9, 3.1, 4.9, 1.5, 'versicolor'),
            (5.5, 2.3, 4.0, 1.3, 'versicolor'),
            
            # virginica samples
            (6.3, 3.3, 6.0, 2.5, 'virginica'),
            (5.8, 2.7, 5.1, 1.9, 'virginica'),
            (7.1, 3.0, 5.9, 2.1, 'virginica')
        ]
        
        date_added = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert data into the database
        for sample in iris_samples:
            cursor.execute('''
            INSERT INTO iris_flowers 
            (sepal_length, sepal_width, petal_length, petal_width, species, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (*sample, date_added))
        
        print(f"Added {len(iris_samples)} iris samples to the database")
    
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