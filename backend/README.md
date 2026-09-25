# Backend Architecture Specification

* **Language & Runtime:** Python 3.11+
* **Framework:** FastAPI
* **Data Validation & DTO:** Pydantic v2
* **Database Access:** MySQL 8.0 (aiomysql)
* **Inter-Service Communication:** Async REST API via `httpx`
* **Network Topology & Ports:**
  - API Gateway (Public Entrance): `http://localhost:8877/api`
  - Internal Microservices (Docker internal network):
    - `account-service`: Port `8661` (DB: `account_db`)
    - `tuition-service`: Port `8732` (DB: `tuition_db`)
    - `payment-service`: Port `8815` (DB: `payment_db`)
    - `notification-service`: Port `8940` (DB: `notification_db`)

---

## 1. Data Flow

```text
route ──> middleware ──> controller ──> services ──> repository ──> schema ──> database
```

### Data Transition Principles:
1. **`route`**: Receives incoming HTTP requests, maps URL endpoints, specifies HTTP methods, and attaches security middlewares.
2. **`middleware`**: Performs JWT token authentication, authorization checks, global exception trapping, and fail-fast validation.
3. **`controller`**: Parses and validates input parameters (`params`, `query`, `body`), delegates to the `services` layer, and wraps responses via `response_util.py`.
4. **`services`**: Implements core business logic, calculations, policy validation, and orchestrates downstream clients.
5. **`repository`**: Exclusively executes MySQL queries (atomic operations, finds, updates) through the aiomysql async connection pool.
6. **`schema`**: Defines table schemas and Pydantic DTO schemas (Request/Response validation).
7. **`database`**: Reads and writes data to the service's dedicated, isolated MySQL database.

---

## 2. Directory Skeleton

Every microservice under `backend/` strictly adheres to a uniform **Internal Service Skeleton**:

```text
backend/
├── README.md
│
└── {service-name}/                  # Abstract Blueprint for each microservice
    ├── Dockerfile                   # Container build specification
    ├── requirements.txt             # Service dependencies
    ├── .env.example                 # Environment variables template
    │
    └── app/
        ├── main.py                  # Service entrypoint, route inclusion, middleware, lifespan
        │
        ├── config/                  # Configuration Layer
        │   ├── env.py               # Environment loader via pydantic-settings
        │   └── database.py          # aiomysql connection pool & database instance
        │
        ├── routes/                  # 1. ROUTE LAYER
        │   └── [feature]_routes.py  # URL endpoint, method, response model, points to controller
        │
        ├── middlewares/             # 2. MIDDLEWARE LAYER
        │   ├── auth_middleware.py   # JWT verification & authorization guard
        │   └── error_middleware.py  # Global exception handler
        │
        ├── controllers/             # 3. CONTROLLER LAYER
        │   └── [feature]_controller.py # Extracts DTO, invokes service, formats response
        │
        ├── services/                # 4. SERVICE LAYER
        │   └── [feature]_service.py # Core business rules, calculations, saga coordination
        │
        ├── repositories/            # 5. REPOSITORY LAYER
        │   └── [feature]_repository.py # Direct MySQL queries (Atomic updates, find, insert)
        │
        ├── schemas/                 # 6. SCHEMA / MODEL LAYER
        │   ├── [feature]_schema.py  # Pydantic DTOs (Request / Response validation)
        │   └── [feature]_document.py# MySQL table schema definition
        │
        ├── utils/                   # Shared Utilities Layer
        │   ├── response_util.py     # Standardized JSON response formatting (success, data, error)
        │   └── error_util.py        # Custom domain exception classes
        │
        └── clients/                 # Inter-Service Transport Layer (Orchestrator only)
            └── [target]_client.py   # HTTP client (httpx) calling downstream services
```

---

## 3. Layer Responsibilities

| Layer / Folder | Responsibility | Constraints |
| :--- | :--- | :--- |
| **`routes/`** | Declares URL endpoints, HTTP methods (`GET`, `POST`, ...), status codes, route security. | **Must delegate directly to Controller**, no inline business logic or database queries. |
| **`middlewares/`** | JWT authentication, permission guards, global error catching, fail-fast validation. | Returns HTTP 401/403/422 immediately on failure. Contains no business domain rules. |
| **`controllers/`** | Extracts validated inputs, coordinates with the corresponding Service, formats output. | **No business calculations**, no direct database operations. |
| **`services/`** | Core business domain logic, condition verification, orchestrating client calls. | **Completely independent of web layer**: does not accept FastAPI `Request` or `Response` objects. |
| **`repositories/`** | Exclusively executes MySQL operations via aiomysql (atomic `UPDATE`, `INSERT`, `SELECT`). | **No business calculations**, pure data persistence layer. |
| **`schemas/`** | Defines table structures and Pydantic DTOs for request/response validation. | Contains no persistence queries or execution logic. |
| **`config/database.py`**| Manages the `aiomysql` connection pool to the service's dedicated database. | Manages lifecycle via FastAPI `lifespan`. |
| **`clients/`** | Encapsulates HTTP client calls to downstream microservices using `httpx.AsyncClient`. | Only present in orchestrator services. Never directly accesses databases of other services. |

---

## 4. Microservices Rules & Concurrency Principles

1. **Strict Database-per-Service:**
   - Each microservice possesses exclusive ownership of its dedicated logical database.
   - Direct cross-database reads or writes are strictly prohibited. All data sharing occurs via REST APIs.

2. **Concurrency & Data Consistency:**
   - In `repositories`, all state-mutating operations must utilize **Atomic Conditional Updates** (atomic `UPDATE` with `WHERE` conditions and row-level locking).
   - Never perform *Read-then-Update* in application memory to prevent race conditions.

3. **Standardized Error Handling & Response Structure:**
   - All endpoints return a uniform JSON format:
     - Success: `{"success": true, "data": ...}`
     - Error: `{"success": false, "error": {"code": "...", "message": "..."}}`
   - Business errors map to appropriate HTTP status codes (400, 401, 403, 404, 409, 422).

---

## 5. Development Commands

```bash
# Install dependencies for a service
pip install -r requirements.txt

# Run an individual service locally
uvicorn app.main:app --host 0.0.0.0 --port {PORT} --reload

# Start full microservices stack via Docker Compose
docker compose up --build
```
