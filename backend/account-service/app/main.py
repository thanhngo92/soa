from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException

from app.config.database import connect_db, close_db
from app.middlewares.error_middleware import app_error_handler, http_error_handler, generic_error_handler
from app.utils.error_util import AppError
from app.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(title="account-service", version="1.0.0", lifespan=lifespan)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(Exception, generic_error_handler)
app.include_router(router, prefix="/api/accounts")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "account-service"}
