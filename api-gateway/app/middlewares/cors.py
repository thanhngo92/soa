from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.env import settings


def register_cors_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.ALLOWED_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
