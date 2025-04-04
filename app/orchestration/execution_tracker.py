import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ExecutionTracker:
    """Tracks the state of request executions."""
    
    def __init__(self):
        self.executions = {}
    
    def start_execution(self, domain: str, operation: str, request_data: Dict[str, Any]) -> str:
        """Start tracking a new execution.
        
        Args:
            domain: The business domain
            operation: The operation being performed
            request_data: The request data
            
        Returns:
            The unique execution ID
        """
        execution_id = str(uuid.uuid4())
        
        execution = {
            "id": execution_id,
            "domain": domain,
            "operation": operation,
            "start_time": datetime.utcnow(),
            "status": "in_progress",
            "request": request_data,
            "end_time": None,
            "error": None
        }
        
        self.executions[execution_id] = execution
        logger.info(f"Started execution {execution_id} for {domain}.{operation}")
        
        return execution_id
    
    def complete_execution(self, execution_id: str, success: bool, error: Optional[str] = None) -> None:
        """Mark an execution as complete.
        
        Args:
            execution_id: The unique execution ID
            success: Whether the execution succeeded
            error: Error message if failed
        """
        if execution_id not in self.executions:
            logger.warning(f"Attempted to complete unknown execution {execution_id}")
            return
        
        execution = self.executions[execution_id]
        execution["end_time"] = datetime.utcnow()
        execution["status"] = "success" if success else "failed"
        
        if not success and error:
            execution["error"] = error
            logger.error(f"Execution {execution_id} failed: {error}")
        else:
            logger.info(f"Execution {execution_id} completed successfully")
    
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific execution.
        
        Args:
            execution_id: The unique execution ID
            
        Returns:
            The execution details or None if not found
        """
        return self.executions.get(execution_id)