from typing import Any, Dict, List, Optional, Union
from fastapi import Depends
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
import os

from app.config.data_source_config_manager import DataSourceConfigManager
from app.common.errors.custom_exceptions import DatabaseError, ResourceNotFoundError
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class DatabaseClient:
    """Client for database operations."""
    
    def __init__(self, config_manager: DataSourceConfigManager = Depends()):
        self.config_manager = config_manager
        self.engines = {}
        self.sessions = {}
        
        # Direct initialization for SQLite database
        try:
            # Get the absolute path to the database file
            db_path = os.path.join(os.getcwd(), "customer360.db")
            logger.info(f"Using SQLite database at: {db_path}")
            
            # Create SQLite engine directly
            connection_string = f"sqlite:///{db_path}"
            engine = sqlalchemy.create_engine(
                connection_string,
                connect_args={"check_same_thread": False}
            )
            self.engines["default"] = engine
        except Exception as e:
            logger.error(f"Error creating SQLite engine: {str(e)}")
    
    def _get_engine(self, source_id: str = "default"):
        """Get a database engine for the specified source ID."""
        if source_id in self.engines:
            return self.engines[source_id]
        
        # Get the database configuration
        config = self.config_manager.get_data_source_config("database", source_id)
        if not config:
            raise DatabaseError(f"Database configuration not found for source '{source_id}'", source_id)
        
        # Create the engine
        try:
            connection_string = config.get("connection_string")
            if not connection_string:
                raise DatabaseError(f"Missing connection string for database source '{source_id}'", source_id)
            
            engine = sqlalchemy.create_engine(connection_string)
            self.engines[source_id] = engine
            return engine
        except Exception as e:
            logger.error(f"Error creating database engine for source '{source_id}': {str(e)}")
            raise DatabaseError(f"Error connecting to database: {str(e)}", source_id)
    
    def _get_session(self, source_id: str = "default"):
        """Get a database session for the specified source ID."""
        if source_id in self.sessions:
            return self.sessions[source_id]()
        
        # Create a new session factory
        engine = self._get_engine(source_id)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.sessions[source_id] = Session
        return Session()
    
    async def query(self, query: str, params: Optional[Dict[str, Any]] = None, source_id: str = "default") -> List[Dict[str, Any]]:
        """Execute a raw SQL query.
        
        Args:
            query: The SQL query string
            params: Query parameters
            source_id: The database source ID
            
        Returns:
            List of result rows as dictionaries
        """
        params = params or {}
        session = self._get_session(source_id)
        
        try:
            result = session.execute(sqlalchemy.text(query), params)
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            session.commit()
            return rows
        except Exception as e:
            session.rollback()
            logger.error(f"Error executing query on database '{source_id}': {str(e)}")
            raise DatabaseError(f"Error executing query: {str(e)}", source_id)
        finally:
            session.close()
    
    # Example operations for the customer domain
    
    async def get_customer(self, customer_id: str, source_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get a customer by ID.
        
        Args:
            customer_id: The customer ID
            source_id: The database source ID
            
        Returns:
            The customer data or None if not found
        """
        query = "SELECT * FROM customers WHERE customer_id = :customer_id"
        params = {"customer_id": customer_id}
        
        try:
            result = await self.query(query, params, source_id)
            if not result:
                return None
            return result[0]
        except Exception as e:
            raise DatabaseError(f"Error retrieving customer: {str(e)}", source_id)
    
    async def list_customers(self, limit: int = 10, offset: int = 0, source_id: str = "default") -> List[Dict[str, Any]]:
        """List customers with pagination.
        
        Args:
            limit: Maximum number of customers to return
            offset: Pagination offset
            source_id: The database source ID
            
        Returns:
            List of customer records
        """
        query = "SELECT * FROM customers ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params = {"limit": limit, "offset": offset}
        
        try:
            return await self.query(query, params, source_id)
        except Exception as e:
            raise DatabaseError(f"Error listing customers: {str(e)}", source_id)
    
    async def create_customer(self, customer_data: Dict[str, Any], source_id: str = "default") -> Dict[str, Any]:
        """Create a new customer.
        
        Args:
            customer_data: The customer data
            source_id: The database source ID
            
        Returns:
            The created customer record
        """
        # Generate a unique customer ID
        customer_id = f"cust_{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow()
        
        # Prepare the data
        data = {
            "customer_id": customer_id,
            "name": customer_data.get("name"),
            "email": customer_data.get("email"),
            "phone": customer_data.get("phone"),
            "address": customer_data.get("address"),
            "date_of_birth": customer_data.get("date_of_birth"),
            "created_at": now,
            "updated_at": now
        }
        
        # Build the query
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        query = f"INSERT INTO customers ({columns}) VALUES ({placeholders}) RETURNING *"
        
        try:
            result = await self.query(query, data, source_id)
            if not result:
                raise DatabaseError("Failed to create customer", source_id)
            return result[0]
        except Exception as e:
            raise DatabaseError(f"Error creating customer: {str(e)}", source_id)
    
    async def update_customer(self, customer_id: str, customer_data: Dict[str, Any], source_id: str = "default") -> Optional[Dict[str, Any]]:
        """Update an existing customer.
        
        Args:
            customer_id: The customer ID
            customer_data: The updated customer data
            source_id: The database source ID
            
        Returns:
            The updated customer record or None if not found
        """
        # Check if the customer exists
        existing = await self.get_customer(customer_id, source_id)
        if not existing:
            return None
        
        # Prepare the data for update
        data = {k: v for k, v in customer_data.items() if k in ["name", "email", "phone", "address", "date_of_birth"]}
        data["updated_at"] = datetime.utcnow()
        data["customer_id"] = customer_id
        
        # Build the update query
        set_clause = ", ".join(f"{k} = :{k}" for k in data.keys() if k != "customer_id")
        query = f"UPDATE customers SET {set_clause} WHERE customer_id = :customer_id RETURNING *"
        
        try:
            result = await self.query(query, data, source_id)
            if not result:
                return None
            return result[0]
        except Exception as e:
            raise DatabaseError(f"Error updating customer: {str(e)}", source_id)
    
    async def delete_customer(self, customer_id: str, source_id: str = "default") -> bool:
        """Delete a customer.
        
        Args:
            customer_id: The customer ID
            source_id: The database source ID
            
        Returns:
            True if deleted, False if not found
        """
        # Check if the customer exists
        existing = await self.get_customer(customer_id, source_id)
        if not existing:
            return False
        
        query = "DELETE FROM customers WHERE customer_id = :customer_id"
        params = {"customer_id": customer_id}
        
        try:
            await self.query(query, params, source_id)
            return True
        except Exception as e:
            raise DatabaseError(f"Error deleting customer: {str(e)}", source_id)
    
    async def get_customer_features(self, customer_id: str, source_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get customer features from the feature store.
        
        Args:
            customer_id: The customer ID
            source_id: The database source ID
            
        Returns:
            The customer features or None if not found
        """
        # Query the features from the customer_features table
        query = "SELECT * FROM customer_features WHERE customer_id = :customer_id"
        params = {"customer_id": customer_id}
        
        try:
            result = await self.query(query, params, source_id)
            if not result:
                return None
            return result[0]
        except Exception as e:
            raise DatabaseError(f"Error retrieving customer features: {str(e)}", source_id)
    
    async def get_customer_credit_score(self, customer_id: str, source_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get a customer's credit score.
        
        Args:
            customer_id: The customer ID
            source_id: The database source ID
            
        Returns:
            The credit score data or None if not found
        """
        query = "SELECT * FROM credit_scores WHERE customer_id = :customer_id"
        params = {"customer_id": customer_id}
        
        try:
            result = await self.query(query, params, source_id)
            if not result:
                return None
            return result[0]
        except Exception as e:
            raise DatabaseError(f"Error retrieving credit score: {str(e)}", source_id)
    
    async def get_customer_recent_orders(self, customer_id: str, limit: int = 5, source_id: str = "default") -> List[Dict[str, Any]]:
        """Get a customer's recent orders.
        
        Args:
            customer_id: The customer ID
            limit: Maximum number of orders to return
            source_id: The database source ID
            
        Returns:
            List of recent orders
        """
        query = "SELECT * FROM orders WHERE customer_id = :customer_id ORDER BY order_date DESC LIMIT :limit"
        params = {"customer_id": customer_id, "limit": limit}
        
        try:
            return await self.query(query, params, source_id)
        except Exception as e:
            raise DatabaseError(f"Error retrieving recent orders: {str(e)}", source_id)
    
    async def get_customer_churn_prediction(self, customer_id: str, source_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get the churn prediction for a customer.
        
        Args:
            customer_id: The customer ID
            source_id: The database source ID
            
        Returns:
            The churn prediction data or None if not found
        """
        query = "SELECT * FROM churn_predictions WHERE customer_id = :customer_id ORDER BY created_at DESC LIMIT 1"
        params = {"customer_id": customer_id}
        
        try:
            result = await self.query(query, params, source_id)
            if not result:
                return None
            return result[0]
        except Exception as e:
            raise DatabaseError(f"Error retrieving churn prediction: {str(e)}", source_id)
