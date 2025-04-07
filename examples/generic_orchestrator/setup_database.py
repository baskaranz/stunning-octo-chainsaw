#!/usr/bin/env python3
"""
Generic Orchestrator Example - Database Setup

This script sets up the database for the generic orchestrator example.
It creates all necessary tables and populates them with sample data.
"""

import os
import argparse
from pathlib import Path
from sqlalchemy import create_engine

# Import the database model
from database_model import populate_database

def create_database(db_path=None):
    """Create and populate the database with sample data."""
    # Default database path if not specified
    if db_path is None:
        # Place the database in the same directory as this script
        script_dir = Path(__file__).parent
        db_path = script_dir / "orchestrator_example.db"
    
    # Convert to string if it's a Path object
    db_path = str(db_path)
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create the database directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    # Create a SQLite database connection
    print(f"Creating new database at: {db_path}")
    connection_string = f"sqlite:///{db_path}"
    engine = create_engine(
        connection_string,
        connect_args={"check_same_thread": False}
    )
    
    # Populate the database with sample data
    populate_database(engine)
    
    print(f"Database setup complete. Database located at: {db_path}")
    return db_path

def main():
    """Main function to parse arguments and set up the database."""
    parser = argparse.ArgumentParser(description="Set up the database for the generic orchestrator example")
    parser.add_argument("--path", help="Custom path for the database file")
    
    args = parser.parse_args()
    
    # Create the database
    db_path = create_database(args.path)
    
    # Print confirmation
    print("\nSample database is ready for the generic orchestrator example.")
    print(f"Location: {db_path}")
    print("\nYou can now start the mock ML services with:")
    print("python examples/generic_orchestrator/mock_ml_services.py")
    print("\nThen run the API with:")
    print("python main.py")
    
if __name__ == "__main__":
    main()