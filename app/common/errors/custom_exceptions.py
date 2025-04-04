from typing import Any, Dict, List, Optional

class OrchestratorError(Exception):
    """Base exception for all orchestrator errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ConfigurationError(OrchestratorError):
    """Exception raised for configuration-related errors."""
    pass

class DataSourceError(OrchestratorError):
    """Exception raised for data source operation errors."""
    def __init__(self, message: str, source_type: str, source_name: Optional[str] = None):
        self.source_type = source_type
        self.source_name = source_name
        super().__init__(f"Data source error ({source_type}{f'/{source_name}' if source_name else ''}): {message}")

class DatabaseError(DataSourceError):
    """Exception raised for database operation errors."""
    def __init__(self, message: str, source_name: Optional[str] = None):
        super().__init__(message, "database", source_name)

class ApiError(DataSourceError):
    """Exception raised for API operation errors."""
    def __init__(self, message: str, source_name: Optional[str] = None, status_code: Optional[int] = None):
        self.status_code = status_code
        error_message = f"{message}{f' (Status: {status_code})' if status_code else ''}"
        super().__init__(error_message, "api", source_name)

class FeastError(DataSourceError):
    """Exception raised for Feast feature store operation errors."""
    def __init__(self, message: str, source_name: Optional[str] = None):
        super().__init__(message, "feast", source_name)

class ModelError(DataSourceError):
    """Exception raised for ML model operation errors."""
    def __init__(self, message: str, source_name: Optional[str] = None):
        super().__init__(message, "ml", source_name)

class ValidationError(OrchestratorError):
    """Exception raised for validation errors."""
    def __init__(self, message: str, errors: Optional[Dict[str, str]] = None):
        self.errors = errors or {}
        super().__init__(message)

class ResourceNotFoundError(OrchestratorError):
    """Exception raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type.title()} with ID '{resource_id}' not found")

class AuthorizationError(OrchestratorError):
    """Exception raised for authorization-related errors."""
    pass
