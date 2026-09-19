# API Gateway Architecture Specification

The API Gateway acts as the **Reverse Proxy & Centralized Entry Point** for all downstream Microservices, built with **Python + FastAPI + HTTPX**.

* **Language & Runtime:** Python 3.11+
* **Framework:** FastAPI (ASGI Uvicorn Server)
* **HTTP Client:** HTTPX (Async Transport Engine)
* **Port:** `8877`
* **Allowed Origin (CORS):** `http://localhost:3659` (Frontend)
* **Downstream Target:** Internal Docker Microservices

---

## 1. Request Lifecycle & Data Flow

```text
client ──> cors/security ──> service resolution ──> async proxy transport ──> downstream service ──> response relay
```

### Processing Principles:
1. **`client`**: Sends HTTP requests to the public ingress address `http://localhost:8877/api/{service}/{path}`.
2. **`cors/security`**: Validates request origin, HTTP method, and headers against the configured CORS policy.
3. **`service resolution`**: Parses the `{service}` identifier from the URL path to resolve the target downstream microservice Base URL.
4. **`async proxy transport`**: Reconstructs the HTTP request (Method, Path, Query Params, Headers, Body) and asynchronously forwards it via `httpx.AsyncClient`.
5. **`downstream service`**: Internal microservice processes the request and returns the response payload.
6. **`response relay`**: Gateway receives upstream response and forwards it unchanged (Status Code, Response Body, Content-Type) back to the client.

---

## 2. Directory Skeleton

```text
api-gateway/
├── Dockerfile                   # Container build specification
├── requirements.txt             # Gateway dependencies (FastAPI, Uvicorn, HTTPX, Pydantic-settings)
├── .env.example                 # Downstream services URL template
├── README.md
│
└── app/
    ├── main.py                  # Gateway entrypoint, CORS setup, proxy routing, lifespan
    │
    ├── config/                  # Configuration Layer
    │   └── env.py               # Downstream service URLs mapping from environment
    │
    ├── middlewares/             # Gateway Middleware Layer
    │   ├── cors.py              # Cross-Origin Resource Sharing policy
    │   └── logging.py           # Access request/response logging
    │
    └── utils/                   # Proxy Utilities
        └── forwarder.py         # HTTP header sanitization & async streaming forwarder
```

---

## 3. Layer Responsibilities

| Layer / Folder | Responsibility | Constraints |
| :--- | :--- | :--- |
| **`config/`** | Reads and manages internal microservice URLs from environment variables. | No hardcoded IPs/Ports in source code. |
| **`middlewares/`** | Handles centralized CORS, request logging, and latency measurements. | Must be low-latency, non-blocking asynchronous execution. |
| **`utils/forwarder.py`** | Sanitizes hop-by-hop headers (`host`, `connection`), wraps and forwards payloads via HTTPX. | Must preserve security authentication headers (`Authorization: Bearer ...`). |
| **`main.py`** | Initializes FastAPI application, registers middlewares, exposes `/health` endpoint, defines dynamic proxy route. | **Strictly no business logic**, no database access. Exclusively network ingress coordination. |

---

## 4. Routing & Proxy Architecture Rules

1. **Service Resolution Policy:**
   - Valid URL path format: `/api/{service_name}/{endpoint_path}`.
   - Gateway maps `{service_name}` to corresponding environment variables:
     `{service_name}` $\longrightarrow$ `{SERVICE_NAME}_SERVICE_URL`
   - If `{service_name}` is not registered in the service directory, returns `404 Not Found`.

2. **Header & Security Propagation:**
   - **Strip:** Hop-by-hop headers at the transport layer (`Host`, `Connection`, `Transfer-Encoding`).
   - **Propagate:** Preserves `Authorization`, `Content-Type`, and `Accept` headers to downstream services.

3. **Fault Tolerance & Timeouts:**
   - Default HTTP client request timeout is set to `30.0s`.
   - If a downstream service is unreachable or times out, returns standardized JSON with `502 Bad Gateway` or `504 Gateway Timeout`.

4. **Health Check Endpoint:**
   - Exposes `GET /health` to verify gateway operational status for Docker container healthchecks.

---

## 5. Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run Gateway independently (Local Dev Mode)
uvicorn app.main:app --host 0.0.0.0 --port 8877 --reload

# Build and start via Docker Compose
docker compose up --build api-gateway
```
