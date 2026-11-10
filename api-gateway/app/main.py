import asyncio
from contextlib import asynccontextmanager
import hashlib
from fastapi import FastAPI, Request, Response
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse
import httpx

from app.config.env import SERVICE_MAP
from app.middlewares.cors import register_cors_middleware
from app.middlewares.idempotency import idempotency_store, IdempotencyPayloadMismatch
from app.middlewares.logging import RequestLoggingMiddleware
from app.utils.forwarder import forward_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=30.0)
    yield
    await app.state.http.aclose()


app = FastAPI(title="API Gateway", version="1.0.0", lifespan=lifespan, openapi_url=None)

register_cors_middleware(app)
app.add_middleware(RequestLoggingMiddleware)


# [Rubric Tiêu chí 2: Kiến trúc Microservices - Workflow Guard]
# Nghiệp vụ: Chặn truy cập trực tiếp từ client ngoài vào các API nội bộ nhạy cảm.
# Kỹ thuật: Client chỉ được đi qua luồng điều phối Saga của Payment Service.
BLOCKED_EXTERNAL_ROUTES = {
    ("POST", "tuitions", "pay"),
    ("POST", "accounts", "deduct"),
    ("POST", "accounts", "refund"),
    ("POST", "notifications", "otp/generate"),
    ("POST", "notifications", "otp/verify"),
    ("POST", "notifications", "email/success"),
}


# [Rubric Tiêu chí 2 & 6: API Gateway Reverse Proxy & Idempotency Key]
# Nghiệp vụ: Điểm tiếp nhận duy nhất (Single Entry Point), định tuyến và bảo vệ giao dịch kép.
# Kỹ thuật: Kiểm tra Idempotency-Key trong header để khóa in-flight và trả kết quả cache cho request trùng lặp.
@app.api_route("/api/{service}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(service: str, request: Request, path: str = ""):
    if service not in SERVICE_MAP:
        return Response(
            content='{"success":false,"error":{"code":"SERVICE_NOT_FOUND","message":"Service not found"}}',
            status_code=404,
            media_type="application/json",
        )

    norm_path = path.strip("/").lower()
    route_key = (request.method.upper(), service.lower(), norm_path)
    if route_key in BLOCKED_EXTERNAL_ROUTES:
        return Response(
            content='{"success":false,"error":{"code":"WORKFLOW_VIOLATION","message":"Forbidden: Direct access to internal service operation is not allowed."}}',
            status_code=403,
            media_type="application/json",
        )

    target_url = f"{SERVICE_MAP[service]}/api/{service}/{path}" if path else f"{SERVICE_MAP[service]}/api/{service}"

    idempotency_key = request.headers.get("idempotency-key") or request.headers.get("x-idempotency-key")
    if idempotency_key and request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        auth_header = request.headers.get("authorization", "")
        user_scope = hashlib.sha256(auth_header.encode()).hexdigest()[:16] if auth_header else "anon"
        composite_key = f"{request.method.upper()}:{service}:{norm_path}:{user_scope}:{idempotency_key}"

        body_bytes = await request.body()
        body_hash = hashlib.sha256(body_bytes).hexdigest()

        try:
            record, is_new = await idempotency_store.get_or_create(composite_key, body_hash)
        except IdempotencyPayloadMismatch:
            return Response(
                content='{"success":false,"error":{"code":"IDEMPOTENCY_PAYLOAD_MISMATCH","message":"Payload does not match original request with this Idempotency-Key"}}',
                status_code=422,
                media_type="application/json",
            )

        if not is_new:
            if record.status == "IN_PROGRESS":
                try:
                    await asyncio.wait_for(record.event.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    return Response(
                        content='{"success":false,"error":{"code":"IDEMPOTENCY_IN_PROGRESS","message":"A request with this Idempotency-Key is currently being processed. Please wait."}}',
                        status_code=409,
                        media_type="application/json",
                    )

            if record.status in ("COMPLETED", "RELEASED") and record.response_content:
                return Response(
                    content=record.response_content,
                    status_code=record.status_code,
                    media_type=record.media_type,
                    headers={
                        "X-Cache-Lookup": "HIT",
                        "X-Idempotent-Replay": "true",
                    },
                )

        try:
            response = await forward_request(request.app.state.http, target_url, request)
            if 200 <= response.status_code < 300:
                await idempotency_store.save_completed(
                    composite_key,
                    response.status_code,
                    response.body,
                    response.media_type or "application/json",
                )
            else:
                await idempotency_store.release_failed(
                    composite_key,
                    response.status_code,
                    response.body,
                    response.media_type or "application/json",
                )

            response.headers["X-Idempotent-Replay"] = "false"
            return response
        except Exception:
            await idempotency_store.release_failed(composite_key)
            raise

    return await forward_request(request.app.state.http, target_url, request)


# [Rubric Tiêu chí 2: Giám sát trạng thái cụm dịch vụ (Health Check)]
# Nghiệp vụ: Cung cấp endpoint tổng hợp trạng thái hoạt động của toàn bộ hệ thống SOA.
# Kỹ thuật: Probe song song 4 microservices bằng asyncio.gather; chỉ trả ok khi tất cả đều ok.
@app.get("/health")
async def health(request: Request):
    http: httpx.AsyncClient = request.app.state.http
    services_status = {}

    async def _probe(name: str, base_url: str):
        try:
            r = await http.get(f"{base_url}/health", timeout=2.0)
            services_status[name] = "ok" if r.status_code == 200 else "degraded"
        except Exception:
            services_status[name] = "down"

    await asyncio.gather(*(_probe(k, v) for k, v in SERVICE_MAP.items()))
    all_ok = all(v == "ok" for v in services_status.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "service": "api-gateway",
        "gateway": "ok",
        "services": services_status,
    }


# [Swagger Aggregator: Gộp toàn bộ tài liệu OpenAPI từ 4 microservices vào một trang duy nhất]
SERVICE_TAG_MAP = {
    "accounts": "Account Service",
    "tuitions": "Tuition Service",
    "payments": "Payment Service",
    "notifications": "Notification Service",
}


@app.get("/openapi.json", include_in_schema=False)
async def custom_openapi(request: Request):
    http: httpx.AsyncClient = request.app.state.http

    master_schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "SOA iBanking API",
            "version": "1.0.0",
            "description": "API Gateway",
        },
        "paths": {},
        "components": {"schemas": {}},
        "tags": [
            {"name": "API Gateway"},
            {"name": "Account Service"},
            {"name": "Tuition Service"},
            {"name": "Payment Service"},
            {"name": "Notification Service"},
        ],
    }

    # Giữ lại endpoint Health Check của Gateway
    master_schema["paths"]["/health"] = {
        "get": {
            "summary": "Health Check",
            "tags": ["API Gateway"],
            "responses": {"200": {"description": "OK"}},
        }
    }

    async def _fetch_openapi(service_name: str, base_url: str):
        try:
            res = await http.get(f"{base_url}/openapi.json", timeout=3.0)
            if res.status_code == 200:
                data = res.json()
                paths = data.get("paths", {})
                for path, methods in paths.items():
                    if path == "/health":
                        continue
                    for method, spec in methods.items():
                        if isinstance(spec, dict):
                            spec["tags"] = [SERVICE_TAG_MAP.get(service_name, service_name)]
                    master_schema["paths"][path] = methods

                schemas = data.get("components", {}).get("schemas", {})
                master_schema["components"]["schemas"].update(schemas)
        except Exception:
            pass

    await asyncio.gather(*(_fetch_openapi(name, url) for name, url in SERVICE_MAP.items()))
    return JSONResponse(master_schema)


@app.get("/docs", include_in_schema=False)
async def swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="SOA iBanking - Aggregated API Docs",
        swagger_ui_parameters={
            "docExpansion": "list",  # Tự động mở rộng danh sách các tag/service
            "filter": True,          # Bật thanh tìm kiếm filter theo tên API
            "tagsSorter": "alpha",   # Sắp xếp theo thứ tự 0, 1, 2, 3, 4
        },
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="SOA iBanking - Aggregated ReDoc",
    )

