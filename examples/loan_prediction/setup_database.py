#!/usr/bin/env python3
"""
Loan Prediction Example - Database Setup

This script creates a SQLite database with sample customer data
for use with the loan prediction example.
"""

import os
import sqlite3
import sys
from pathlib import Path

# Sample applicant data with financial information
APPLICANTS = {
    "app_1001": {
        "applicant_id": "app_1001",
        "name": "Alex Johnson",
        "email": "alex.johnson@example.com",
        "age": 35,
        "created_at": "2023-12-15T10:30:00Z"
    },
    "app_1002": {
        "applicant_id": "app_1002",
        "name": "Maria Garcia",
        "email": "maria.garcia@example.com",
        "age": 42,
        "created_at": "2023-11-22T14:45:00Z"
    },
    "app_1003": {
        "applicant_id": "app_1003",
        "name": "James Wilson",
        "email": "james.wilson@example.com",
        "age": 28,
        "created_at": "2024-01-05T09:15:00Z"
    },
    "app_1004": {
        "applicant_id": "app_1004",
        "name": "Sarah Chen",
        "email": "sarah.chen@example.com",
        "age": 31,
        "created_at": "2024-02-18T11:20:00Z"
    },
    "app_1005": {
        "applicant_id": "app_1005",
        "name": "Robert Kim",
        "email": "robert.kim@example.com",
        "age": 45,
        "created_at": "2023-10-30T16:00:00Z"
    }
}

# Financial data for each applicant
FINANCIAL_DATA = {
    "app_1001": {
        "applicant_id": "app_1001",
        "annual_income": 75000,
        "credit_score": 710,
        "debt_to_income": 0.28,
        "employment_years": 8,
        "loan_amount": 250000,
        "loan_term": 30,
        "loan_purpose": "Home Purchase"
    },
    "app_1002": {
        "applicant_id": "app_1002",
        "annual_income": 120000,
        "credit_score": 780,
        "debt_to_income": 0.15,
        "employment_years": 15,
        "loan_amount": 350000,
        "loan_term": 15,
        "loan_purpose": "Refinance"
    },
    "app_1003": {
        "applicant_id": "app_1003",
        "annual_income": 45000,
        "credit_score": 650,
        "debt_to_income": 0.36,
        "employment_years": 2,
        "loan_amount": 180000,
        "loan_term": 30,
        "loan_purpose": "Home Purchase"
    },
    "app_1004": {
        "applicant_id": "app_1004",
        "annual_income": 95000,
        "credit_score": 720,
        "debt_to_income": 0.22,
        "employment_years": 6,
        "loan_amount": 320000,
        "loan_term": 30,
        "loan_purpose": "Home Purchase"
    },
    "app_1005": {
        "applicant_id": "app_1005",
        "annual_income": 150000,
        "credit_score": 800,
        "debt_to_income": 0.10,
        "employment_years": 20,
        "loan_amount": 500000,
        "loan_term": 15,
        "loan_purpose": "Refinance"
    }
}

# Previous loan application history
LOAN_HISTORY = {
    "app_1001": {
        "applicant_id": "app_1001",
        "previous_applications": 2,
        "approved_loans": 1,
        "rejected_loans": 1, 
        "current_loans": 1,
        "total_current_debt": 180000
    },
    "app_1002": {
        "applicant_id": "app_1002",
        "previous_applications": 3,
        "approved_loans": 3,
        "rejected_loans": 0,
        "current_loans": 2,
        "total_current_debt": 210000
    },
    "app_1003": {
        "applicant_id": "app_1003",
        "previous_applications": 1,
        "approved_loans": 0,
        "rejected_loans": 1,
        "current_loans": 0,
        "total_current_debt": 15000
    },
    "app_1004": {
        "applicant_id": "app_1004",
        "previous_applications": 2,
        "approved_loans": 2,
        "rejected_loans": 0,
        "current_loans": 1,
        "total_current_debt": 200000
    },
    "app_1005": {
        "applicant_id": "app_1005",
        "previous_applications": 4,
        "approved_loans": 4,
        "rejected_loans": 0,
        "current_loans": 1,
        "total_current_debt": 320000
    }
}

def create_database():
    """Create the SQLite database with sample data."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    db_path = script_dir / "loan_prediction.db"
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create applicants table
    cursor.execute('''
    CREATE TABLE applicants (
        applicant_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        age INTEGER,
        created_at TEXT
    )
    ''')
    
    # Create financial_data table
    cursor.execute('''
    CREATE TABLE financial_data (
        applicant_id TEXT PRIMARY KEY,
        annual_income REAL,
        credit_score INTEGER,
        debt_to_income REAL,
        employment_years INTEGER,
        loan_amount REAL,
        loan_term INTEGER,
        loan_purpose TEXT,
        FOREIGN KEY (applicant_id) REFERENCES applicants (applicant_id)
    )
    ''')
    
    # Create loan_history table
    cursor.execute('''
    CREATE TABLE loan_history (
        applicant_id TEXT PRIMARY KEY,
        previous_applications INTEGER,
        approved_loans INTEGER,
        rejected_loans INTEGER,
        current_loans INTEGER,
        total_current_debt REAL,
        FOREIGN KEY (applicant_id) REFERENCES applicants (applicant_id)
    )
    ''')
    
    # Insert sample data into applicants table
    for applicant in APPLICANTS.values():
        cursor.execute('''
        INSERT INTO applicants (applicant_id, name, email, age, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            applicant['applicant_id'],
            applicant['name'],
            applicant['email'],
            applicant['age'],
            applicant['created_at']
        ))
    
    # Insert sample data into financial_data table
    for data in FINANCIAL_DATA.values():
        cursor.execute('''
        INSERT INTO financial_data (
            applicant_id, annual_income, credit_score, debt_to_income,
            employment_years, loan_amount, loan_term, loan_purpose
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['applicant_id'],
            data['annual_income'],
            data['credit_score'],
            data['debt_to_income'],
            data['employment_years'],
            data['loan_amount'],
            data['loan_term'],
            data['loan_purpose']
        ))
    
    # Insert sample data into loan_history table
    for history in LOAN_HISTORY.values():
        cursor.execute('''
        INSERT INTO loan_history (
            applicant_id, previous_applications, approved_loans,
            rejected_loans, current_loans, total_current_debt
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            history['applicant_id'],
            history['previous_applications'],
            history['approved_loans'],
            history['rejected_loans'],
            history['current_loans'],
            history['total_current_debt']
        ))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at {db_path}")
    return str(db_path)

if __name__ == "__main__":
    create_database()