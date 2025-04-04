from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app.common.errors.custom_exceptions import (
    OrchestratorError,
    ConfigurationError,
    DataSourceError,
    ValidationError,
    ResourceNotFoundError,
    AuthorizationError
)
from app.common.utils.logging_utils import get_logger

logger = get_logger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI's RequestValidationError."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation error",
            "errors": exc.errors()
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle Starlette's HTTPException."""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )

async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    """Handle ResourceNotFoundError."""
    logger.warning(f"Resource not found: {exc}")
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": str(exc)
        }
    )

async def authorization_error_handler(request: Request, exc: AuthorizationError):
    """Handle AuthorizationError."""
    logger.warning(f"Authorization error: {exc}")
    return JSONResponse(
        status_code=403,
        content={
            "status": "error",
            "message": str(exc)
        }
    )

async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle ValidationError."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": str(exc),
            "errors": exc.errors
        }
    )

async def data_source_error_handler(request: Request, exc: DataSourceError):
    """Handle DataSourceError."""
    logger.error(f"Data source error: {exc}")
    return JSONResponse(
        status_code=502,  # Bad Gateway for external service errors
        content={
            "status": "error",
            "message": str(exc)
        }
    )

async def configuration_error_handler(request: Request, exc: ConfigurationError):
    """Handle ConfigurationError."""
    logger.error(f"Configuration error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc)
        }
    )

async def orchestrator_error_handler(request: Request, exc: OrchestratorError):
    """Handle generic OrchestratorError."""
    logger.error(f"Orchestrator error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc)
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred"
        }
    )

def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ResourceNotFoundError, resource_not_found_handler)
    app.add_exception_handler(AuthorizationError, authorization_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(DataSourceError, data_source_error_handler)
    app.add_exception_handler(ConfigurationError, configuration_error_handler)
    app.add_exception_handler(OrchestratorError, orchestrator_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
