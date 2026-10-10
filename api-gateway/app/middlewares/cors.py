from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.env import settings


def register_cors_middleware(app: FastAPI) -> None:
    origins = [o.strip() for o in settings.ALLOWED_ORIGIN.split(",") if o.strip()]
    if not origins:
        origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
