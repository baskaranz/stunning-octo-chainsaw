"""
Generic Orchestrator Example - Database Extensions

This module extends the DatabaseClient with methods needed for the
generic orchestrator example.
"""

from typing import Dict, Any, Optional, List
from app.adapters.database.database_client import DatabaseClient
from app.common.errors.custom_exceptions import DatabaseError
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

def patch_database_client():
    """
    Patch the DatabaseClient with methods for the generic orchestrator example.
    """
    
    async def get_credit_profile_by_customer_id(self, customer_id: str, source_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get a customer's credit profile.
        
        Args:
            customer_id: The customer ID
            source_id: The database source ID
            
        Returns:
            The credit profile data or None if not found
        """
        query = """
        SELECT 
          *
        FROM 
          credit_profiles
        WHERE 
          customer_id = :customer_id
        ORDER BY
          updated_at DESC
        LIMIT 1
        """
        params = {"customer_id": customer_id}
        
        try:
            result = await self.query(query, params, source_id)
            if not result:
                return None
            return result[0]
        except Exception as e:
            logger.error(f"Error retrieving credit profile: {str(e)}")
            raise DatabaseError(f"Error retrieving credit profile: {str(e)}", source_id)
    
    async def get_customer_preferences(self, customer_id: str, source_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get a customer's preferences.
        
        Args:
            customer_id: The customer ID
            source_id: The database source ID
            
        Returns:
            The customer preferences or None if not found
        """
        query = """
        SELECT 
          *
        FROM 
          customer_preferences
        WHERE 
          customer_id = :customer_id
        ORDER BY
          updated_at DESC
        LIMIT 1
        """
        params = {"customer_id": customer_id}
        
        try:
            result = await self.query(query, params, source_id)
            if not result:
                return None
            return result[0]
        except Exception as e:
            logger.error(f"Error retrieving customer preferences: {str(e)}")
            raise DatabaseError(f"Error retrieving customer preferences: {str(e)}", source_id)
    
    async def get_customer_recent_purchases(self, customer_id: str, limit: int = 5, source_id: str = "default") -> List[Dict[str, Any]]:
        """Get a customer's recent purchases with product details.
        
        Args:
            customer_id: The customer ID
            limit: Maximum number of purchases to return
            source_id: The database source ID
            
        Returns:
            List of recent purchases with product details
        """
        query = """
        SELECT 
          p.id as purchase_id,
          p.customer_id,
          p.product_id,
          p.purchase_date,
          p.quantity,
          p.price_paid,
          p.discount_amount,
          p.payment_method,
          p.order_id,
          pr.name as product_name,
          pr.category,
          pr.subcategory,
          pr.price as list_price,
          pr.price_tier
        FROM 
          purchases p
          JOIN products pr ON p.product_id = pr.product_id
        WHERE 
          p.customer_id = :customer_id
        ORDER BY
          p.purchase_date DESC
        LIMIT :limit
        """
        params = {"customer_id": customer_id, "limit": limit}
        
        try:
            return await self.query(query, params, source_id)
        except Exception as e:
            logger.error(f"Error retrieving recent purchases: {str(e)}")
            raise DatabaseError(f"Error retrieving recent purchases: {str(e)}", source_id)
    
    async def get_product_recommendations(self, customer_id: str, category: Optional[str] = None, limit: int = 5, source_id: str = "default") -> List[Dict[str, Any]]:
        """Get product recommendations based on customer preferences and purchase history.
        
        Args:
            customer_id: The customer ID
            category: Optional category to filter by
            limit: Maximum number of recommendations
            source_id: The database source ID
            
        Returns:
            List of recommended products
        """
        # First, get the customer's preferences
        prefs = await self.get_customer_preferences(customer_id, source_id)
        
        # Build the query based on preferences
        # This is a simplified recommendation algorithm that just finds popular products
        # in the customer's preferred categories or the specified category
        query_parts = [
            "SELECT",
            "  p.product_id,",
            "  p.name,",
            "  p.description,",
            "  p.category,",
            "  p.subcategory,",
            "  p.price,",
            "  p.price_tier,",
            "  COUNT(pu.id) as purchase_count",
            "FROM",
            "  products p",
            "  LEFT JOIN purchases pu ON p.product_id = pu.product_id",
            "WHERE",
            "  p.is_active = 1"
        ]
        
        params = {}
        
        # Filter by category if specified
        if category:
            query_parts.append("  AND p.category = :category")
            params["category"] = category
        # Otherwise use preferred categories if available
        elif prefs and prefs.get("preferred_categories"):
            preferred_cats = prefs["preferred_categories"].split(",")
            if preferred_cats and preferred_cats[0]:
                placeholders = [f":cat{i}" for i in range(len(preferred_cats))]
                query_parts.append(f"  AND p.category IN ({', '.join(placeholders)})")
                for i, cat in enumerate(preferred_cats):
                    params[f"cat{i}"] = cat.strip()
        
        # Complete the query
        query_parts.extend([
            "GROUP BY",
            "  p.product_id",
            "ORDER BY",
            "  purchase_count DESC,",
            "  p.release_date DESC",
            "LIMIT :limit"
        ])
        
        # Add limit parameter
        params["limit"] = limit
        
        # Join the query parts
        query = "\n".join(query_parts)
        
        try:
            return await self.query(query, params, source_id)
        except Exception as e:
            logger.error(f"Error retrieving product recommendations: {str(e)}")
            raise DatabaseError(f"Error retrieving product recommendations: {str(e)}", source_id)
    
    # Add the methods to the DatabaseClient class
    setattr(DatabaseClient, "get_credit_profile_by_customer_id", get_credit_profile_by_customer_id)
    setattr(DatabaseClient, "get_customer_preferences", get_customer_preferences)
    setattr(DatabaseClient, "get_customer_recent_purchases", get_customer_recent_purchases)
    setattr(DatabaseClient, "get_product_recommendations", get_product_recommendations)