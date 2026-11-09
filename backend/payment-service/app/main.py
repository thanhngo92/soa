from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
import httpx

from app.core import (
    connect_db,
    close_db,
    AppError,
    app_error_handler,
    http_error_handler,
    validation_error_handler,
    generic_error_handler,
)
from app.payments import router as payments_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    app.state.http = httpx.AsyncClient(timeout=10.0)
    yield
    await app.state.http.aclose()
    await close_db()


app = FastAPI(title="payment-service", version="1.0.0", lifespan=lifespan)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_error_handler)
app.include_router(payments_router, prefix="/api/payments")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "payment-service"}
