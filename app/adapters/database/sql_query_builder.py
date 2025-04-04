from typing import Any, Dict, List, Optional, Union

class SQLQueryBuilder:
    """Utility for building SQL queries."""
    
    @staticmethod
    def build_select_query(table: str, columns: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None, 
                           order_by: Optional[str] = None, limit: Optional[int] = None, 
                           offset: Optional[int] = None) -> tuple[str, Dict[str, Any]]:
        """Build a SELECT query.
        
        Args:
            table: The table name
            columns: List of columns to select (defaults to *)
            where: Dictionary of column-value pairs for WHERE clause
            order_by: ORDER BY clause
            limit: LIMIT clause
            offset: OFFSET clause
            
        Returns:
            Tuple of (query_string, params_dict)
        """
        columns_str = "*" if not columns else ", ".join(columns)
        query = f"SELECT {columns_str} FROM {table}"
        
        params = {}
        where_clauses = []
        
        # Add WHERE conditions
        if where:
            for i, (col, val) in enumerate(where.items()):
                param_name = f"param_{i}"
                where_clauses.append(f"{col} = :{param_name}")
                params[param_name] = val
                
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        # Add ORDER BY
        if order_by:
            query += f" ORDER BY {order_by}"
        
        # Add LIMIT
        if limit is not None:
            query += f" LIMIT {limit}"
        
        # Add OFFSET
        if offset is not None:
            query += f" OFFSET {offset}"
        
        return query, params
    
    @staticmethod
    def build_insert_query(table: str, data: Dict[str, Any], returning: bool = True) -> tuple[str, Dict[str, Any]]:
        """Build an INSERT query.
        
        Args:
            table: The table name
            data: Dictionary of column-value pairs to insert
            returning: Whether to include RETURNING *
            
        Returns:
            Tuple of (query_string, params_dict)
        """
        columns = list(data.keys())
        columns_str = ", ".join(columns)
        
        placeholders = [f":{col}" for col in columns]
        placeholders_str = ", ".join(placeholders)
        
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders_str})"
        
        if returning:
            query += " RETURNING *"
        
        return query, data
    
    @staticmethod
    def build_update_query(table: str, data: Dict[str, Any], where: Dict[str, Any], returning: bool = True) -> tuple[str, Dict[str, Any]]:
        """Build an UPDATE query.
        
        Args:
            table: The table name
            data: Dictionary of column-value pairs to update
            where: Dictionary of column-value pairs for WHERE clause
            returning: Whether to include RETURNING *
            
        Returns:
            Tuple of (query_string, params_dict)
        """
        params = {}
        
        # Set clause
        set_items = []
        for i, (col, val) in enumerate(data.items()):
            param_name = f"set_{i}"
            set_items.append(f"{col} = :{param_name}")
            params[param_name] = val
        
        set_clause = ", ".join(set_items)
        
        # Where clause
        where_items = []
        for i, (col, val) in enumerate(where.items()):
            param_name = f"where_{i}"
            where_items.append(f"{col} = :{param_name}")
            params[param_name] = val
        
        where_clause = " AND ".join(where_items)
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        if returning:
            query += " RETURNING *"
        
        return query, params
    
    @staticmethod
    def build_delete_query(table: str, where: Dict[str, Any], returning: bool = False) -> tuple[str, Dict[str, Any]]:
        """Build a DELETE query.
        
        Args:
            table: The table name
            where: Dictionary of column-value pairs for WHERE clause
            returning: Whether to include RETURNING *
            
        Returns:
            Tuple of (query_string, params_dict)
        """
        params = {}
        
        # Where clause
        where_items = []
        for i, (col, val) in enumerate(where.items()):
            param_name = f"where_{i}"
            where_items.append(f"{col} = :{param_name}")
            params[param_name] = val
        
        where_clause = " AND ".join(where_items)
        
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        if returning:
            query += " RETURNING *"
        
        return query, params
