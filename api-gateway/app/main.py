from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
import httpx

from app.config.env import SERVICE_MAP
from app.middlewares.cors import register_cors_middleware
from app.middlewares.logging import RequestLoggingMiddleware
from app.utils.forwarder import forward_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=30.0)
    yield
    await app.state.http.aclose()


app = FastAPI(title="API Gateway", version="1.0.0", lifespan=lifespan)

register_cors_middleware(app)
app.add_middleware(RequestLoggingMiddleware)


@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICE_MAP:
        return Response(
            content='{"success":false,"error":{"code":"SERVICE_NOT_FOUND","message":"Service not found"}}',
            status_code=404,
            media_type="application/json",
        )

    target_url = f"{SERVICE_MAP[service]}/api/{service}/{path}"
    return await forward_request(request.app.state.http, target_url, request)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}
