from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.core import (
    connect_db,
    close_db,
    AppError,
    app_error_handler,
    http_error_handler,
    validation_error_handler,
    generic_error_handler,
)
from app.notifications import router as notifications_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(title="notification-service", version="1.0.0", lifespan=lifespan)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_error_handler)
app.include_router(notifications_router, prefix="/api/notifications")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notification-service"}
