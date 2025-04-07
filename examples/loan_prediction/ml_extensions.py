"""
Loan Prediction ML Extensions

This module extends the ModelClient with loan prediction specific methods.
"""

from typing import Dict, Any, Optional
from app.adapters.ml.model_client import ModelClient
from app.common.errors.custom_exceptions import ModelError
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Function to patch the ModelClient with loan prediction methods
def patch_model_client():
    """
    Patch the ModelClient with loan prediction specific methods.
    """
    
    async def predict_loan_approval(self, features: Dict[str, Any], source_id: str = "loan_model") -> Dict[str, Any]:
        """Predict loan approval probability.
        
        Args:
            features: Applicant feature values
            source_id: The ML service source ID
            
        Returns:
            Loan approval prediction result
        """
        try:
            return await self.predict("loan_approval", features, source_id)
        except Exception as e:
            logger.error(f"Error predicting loan approval: {str(e)}")
            raise ModelError(f"Failed to predict loan approval: {str(e)}", source_id)
    
    # Add the method to the ModelClient class
    setattr(ModelClient, "predict_loan_approval", predict_loan_approval)