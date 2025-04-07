"""
Loan Prediction Database Extensions

This module extends the DatabaseClient with loan prediction specific methods.
"""

from typing import Dict, Any, Optional
from app.adapters.database.database_client import DatabaseClient
from app.common.errors.custom_exceptions import DatabaseError
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Function to patch the DatabaseClient with loan prediction methods
def patch_database_client():
    """
    Patch the DatabaseClient with loan prediction specific methods.
    """
    
    async def get_applicant_features(self, applicant_id: str, source_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get loan applicant features.
        
        Args:
            applicant_id: The applicant ID
            source_id: The database source ID
            
        Returns:
            The applicant features or None if not found
        """
        # Use the SQL query as defined in the database configuration
        query = """
        SELECT 
          a.applicant_id,
          a.age,
          f.annual_income,
          f.credit_score,
          f.debt_to_income,
          f.employment_years,
          f.loan_amount,
          f.loan_term,
          f.loan_purpose,
          h.previous_applications,
          h.approved_loans,
          h.rejected_loans,
          h.current_loans,
          h.total_current_debt,
          CASE WHEN h.previous_applications > 0 
               THEN CAST(h.approved_loans AS FLOAT) / h.previous_applications 
               ELSE 0 
          END AS approval_ratio
        FROM 
          applicants a
          JOIN financial_data f ON a.applicant_id = f.applicant_id
          JOIN loan_history h ON a.applicant_id = h.applicant_id
        WHERE 
          a.applicant_id = :applicant_id
        """
        params = {"applicant_id": applicant_id}
        
        try:
            result = await self.query(query, params, source_id)
            if not result:
                return None
            return result[0]
        except Exception as e:
            logger.error(f"Error retrieving applicant features: {str(e)}")
            raise DatabaseError(f"Error retrieving applicant features: {str(e)}", source_id)
    
    # Add the method to the DatabaseClient class
    setattr(DatabaseClient, "get_applicant_features", get_applicant_features)