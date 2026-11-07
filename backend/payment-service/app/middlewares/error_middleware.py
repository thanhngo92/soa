from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.utils.error_util import AppError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handles domain-specific business exceptions with standard format."""
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": exc.detail})


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handles FastAPI/Starlette HTTP exceptions uniformly."""
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        error_payload = detail
    else:
        error_payload = {"code": "HTTP_ERROR", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": error_payload})


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Formats Pydantic/FastAPI request validation errors into standard JSend error structure."""
    errors = exc.errors()
    first_msg = errors[0].get("msg", "Invalid request payload") if errors else "Invalid request payload"
    loc = ".".join(str(x) for x in errors[0].get("loc", []) if x != "body") if errors else ""
    message = f"{loc}: {first_msg}" if loc else first_msg
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": {"code": "VALIDATION_ERROR", "message": message}},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled internal server exceptions."""
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(exc) if str(exc) else "Internal server error"}},
    )
