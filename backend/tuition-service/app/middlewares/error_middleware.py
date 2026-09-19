from fastapi import Request
from fastapi.responses import JSONResponse
from app.utils.error_util import AppError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": exc.detail})


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )
