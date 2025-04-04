#!/usr/bin/env python3
"""
Database Setup for Customer 360 Example

This script sets up a local SQLite database with tables for customers and orders,
and populates them with sample data.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
import random

# Ensure we create the database in the example directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "customer360.db")

# Sample data (same as in the mock services)
CUSTOMERS = {
    "cust_12345": {
        "customer_id": "cust_12345",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "address": "123 Main St, San Francisco, CA 94105",
        "date_of_birth": "1990-01-01",
        "created_at": "2022-03-15T10:30:00Z",
        "updated_at": "2023-04-20T15:45:00Z"
    },
    "cust_67890": {
        "customer_id": "cust_67890",
        "name": "Jane Smith", 
        "email": "jane.smith@example.com",
        "phone": "+0987654321",
        "address": "456 Oak St, New York, NY 10001",
        "date_of_birth": "1985-05-15",
        "created_at": "2020-08-10T14:20:00Z",
        "updated_at": "2023-02-28T09:15:00Z"
    },
    "cust_24680": {
        "customer_id": "cust_24680",
        "name": "Michael Johnson",
        "email": "michael.johnson@example.com",
        "phone": "+1122334455",
        "address": "789 Pine St, Seattle, WA 98101",
        "date_of_birth": "1978-11-30",
        "created_at": "2021-05-22T11:00:00Z",
        "updated_at": "2022-12-15T16:30:00Z"
    }
}

# Sample orders
ORDERS = {
    "cust_12345": [
        {
            "order_id": "ord_98765",
            "customer_id": "cust_12345",
            "order_date": "2023-03-15T14:30:00Z",
            "total_amount": 95.50,
            "status": "Delivered",
            "items_count": 3
        },
        {
            "order_id": "ord_87654",
            "customer_id": "cust_12345",
            "order_date": "2023-02-22T10:15:00Z",
            "total_amount": 120.75,
            "status": "Delivered",
            "items_count": 4
        },
        {
            "order_id": "ord_76543",
            "customer_id": "cust_12345",
            "order_date": "2023-01-10T16:45:00Z",
            "total_amount": 75.20,
            "status": "Delivered",
            "items_count": 2
        }
    ],
    "cust_67890": [
        {
            "order_id": "ord_54321",
            "customer_id": "cust_67890",
            "order_date": "2023-04-05T09:30:00Z",
            "total_amount": 150.00,
            "status": "Processing",
            "items_count": 5
        },
        {
            "order_id": "ord_43210",
            "customer_id": "cust_67890",
            "order_date": "2023-03-20T13:45:00Z",
            "total_amount": 85.99,
            "status": "Delivered",
            "items_count": 3
        }
    ],
    "cust_24680": [
        {
            "order_id": "ord_32109",
            "customer_id": "cust_24680",
            "order_date": "2023-04-10T11:20:00Z",
            "total_amount": 220.50,
            "status": "Shipped",
            "items_count": 6
        },
        {
            "order_id": "ord_21098",
            "customer_id": "cust_24680",
            "order_date": "2023-02-28T15:10:00Z",
            "total_amount": 45.25,
            "status": "Delivered",
            "items_count": 1
        },
        {
            "order_id": "ord_10987",
            "customer_id": "cust_24680",
            "order_date": "2023-01-15T12:35:00Z",
            "total_amount": 130.00,
            "status": "Delivered",
            "items_count": 4
        },
        {
            "order_id": "ord_09876",
            "customer_id": "cust_24680",
            "order_date": "2022-12-05T10:50:00Z",
            "total_amount": 95.75,
            "status": "Delivered",
            "items_count": 3
        }
    ]
}

# Feature data
FEATURES = {
    "cust_12345": {
        "customer_lifetime_value": 2450.75,
        "days_since_last_purchase": 15,
        "purchase_frequency": 2.3,
        "average_order_value": 85.25,
        "total_purchases": 12
    },
    "cust_67890": {
        "customer_lifetime_value": 3750.50,
        "days_since_last_purchase": 5,
        "purchase_frequency": 3.1,
        "average_order_value": 95.80,
        "total_purchases": 18
    },
    "cust_24680": {
        "customer_lifetime_value": 1850.25,
        "days_since_last_purchase": 10,
        "purchase_frequency": 1.5,
        "average_order_value": 110.25,
        "total_purchases": 8
    }
}

# Credit scores
CREDIT_SCORES = {
    "cust_12345": {
        "score": 720,
        "risk_tier": "Low",
        "updated_at": "2023-03-01T00:00:00Z"
    },
    "cust_67890": {
        "score": 680,
        "risk_tier": "Medium",
        "updated_at": "2023-02-15T00:00:00Z"
    },
    "cust_24680": {
        "score": 750,
        "risk_tier": "Low",
        "updated_at": "2023-03-10T00:00:00Z"
    }
}

def setup_database():
    """Set up the SQLite database with tables and sample data."""
    print(f"Creating database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        date_of_birth TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')
    
    # Create orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        order_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL,
        items_count INTEGER NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')
    
    # Create features table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customer_features (
        customer_id TEXT PRIMARY KEY,
        customer_lifetime_value REAL,
        days_since_last_purchase INTEGER,
        purchase_frequency REAL,
        average_order_value REAL,
        total_purchases INTEGER,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')
    
    # Create credit_scores table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS credit_scores (
        customer_id TEXT PRIMARY KEY,
        score INTEGER NOT NULL,
        risk_tier TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')
    
    # Create table for ML predictions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS churn_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT NOT NULL,
        probability REAL NOT NULL,
        risk_level TEXT NOT NULL,
        recommendation TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')
    
    # Insert data into customers table
    for customer_id, customer in CUSTOMERS.items():
        cursor.execute('''
        INSERT OR REPLACE INTO customers 
        (customer_id, name, email, phone, address, date_of_birth, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer["customer_id"],
            customer["name"],
            customer["email"],
            customer["phone"],
            customer["address"],
            customer["date_of_birth"],
            customer["created_at"],
            customer["updated_at"]
        ))
    
    # Insert data into orders table
    for customer_id, orders in ORDERS.items():
        for order in orders:
            cursor.execute('''
            INSERT OR REPLACE INTO orders
            (order_id, customer_id, order_date, total_amount, status, items_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                order["order_id"],
                order["customer_id"],
                order["order_date"],
                order["total_amount"],
                order["status"],
                order["items_count"]
            ))
    
    # Insert data into features table
    for customer_id, features in FEATURES.items():
        cursor.execute('''
        INSERT OR REPLACE INTO customer_features
        (customer_id, customer_lifetime_value, days_since_last_purchase, purchase_frequency, average_order_value, total_purchases)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            customer_id,
            features["customer_lifetime_value"],
            features["days_since_last_purchase"],
            features["purchase_frequency"],
            features["average_order_value"],
            features["total_purchases"]
        ))
    
    # Insert data into credit_scores table
    for customer_id, credit_score in CREDIT_SCORES.items():
        cursor.execute('''
        INSERT OR REPLACE INTO credit_scores
        (customer_id, score, risk_tier, updated_at)
        VALUES (?, ?, ?, ?)
        ''', (
            customer_id,
            credit_score["score"],
            credit_score["risk_tier"],
            credit_score["updated_at"]
        ))
    
    # Generate and insert churn predictions
    for customer_id, features in FEATURES.items():
        # Simple formula to calculate churn probability
        # Lower LTV and higher days since purchase = higher churn probability
        churn_probability = max(0.1, min(0.9, 
            (0.4 - (features["customer_lifetime_value"] / 10000) + (features["days_since_last_purchase"] / 100))
        ))
        
        # Determine risk level
        risk_level = "Low"
        if churn_probability > 0.6:
            risk_level = "High"
        elif churn_probability > 0.3:
            risk_level = "Medium"
        
        # Generate a recommendation based on the risk level
        recommendations = {
            "Low": "Standard Discount Offer",
            "Medium": "Loyalty Program Upgrade",
            "High": "Premium Subscription at Special Rate"
        }
        
        cursor.execute('''
        INSERT OR REPLACE INTO churn_predictions
        (customer_id, probability, risk_level, recommendation, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            customer_id,
            churn_probability,
            risk_level,
            recommendations[risk_level],
            datetime.now().isoformat()
        ))
    
    conn.commit()
    conn.close()
    print("Database setup complete!")
    print(f"Database file created at: {DB_PATH}")
    print("Use this path in your configuration when running the example.")

if __name__ == "__main__":
    setup_database()