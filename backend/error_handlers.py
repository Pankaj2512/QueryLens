"""Custom error handlers and exceptions for QueryLens."""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class QueryLensException(Exception):
    """Base exception for QueryLens."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(QueryLensException):
    """Validation error."""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 400)


class ResourceNotFoundException(QueryLensException):
    """Resource not found error."""
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", "NOT_FOUND", 404)


class DatabaseException(QueryLensException):
    """Database error."""
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR", 500)


class FileOperationException(QueryLensException):
    """File operation error."""
    def __init__(self, message: str):
        super().__init__(message, "FILE_ERROR", 400)


class LLMException(QueryLensException):
    """LLM service error."""
    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR", 500)


async def querylens_exception_handler(request: Request, exc: QueryLensException):
    """Handle QueryLens exceptions."""
    logger.error(f"QueryLens exception: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        }
    )


# Backward compatibility aliases
QueryForgeException = QueryLensException
queryforge_exception_handler = querylens_exception_handler


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors,
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Normalize HTTPException payloads to error contract."""
    detail = exc.detail
    code = "HTTP_ERROR"
    message = "Request failed"
    details = None

    if isinstance(detail, dict):
        code = str(detail.get("code", code))
        message = str(detail.get("message", message))
        details = detail.get("details")
    elif isinstance(detail, str):
        message = detail
    elif detail is not None:
        details = detail

    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=exc.status_code, content=payload)


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        }
    )
