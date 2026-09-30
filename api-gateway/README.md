# API Gateway — Tài Liệu Triển Khai Chi Tiết (Member 3)

> **Dự án:** iBanking Tuition Payment System (SOA)  
> **Người phụ trách:** **Member 3** (Payment Service + API Gateway + Frontend Integration)  
> **Công nghệ:** Python 3.11+ • FastAPI • HTTPX Reverse Proxy Engine  
> **Port:** `8877` (Public Ingress)  
> **Frontend Origin (CORS):** `http://localhost:3659`

---

## 1. Mục Tiêu & Phạm Vi Công Việc

API Gateway là **Cổng vào tập trung duy nhất (Single Entry Point)** cho toàn bộ hệ thống iBanking SOA:
1. **Định tuyến ngược (Reverse Proxy Routing)**: Nhận toàn bộ request từ Frontend và định tuyến đến đúng Microservice tương ứng.
2. **Cấu hình CORS tập trung**: Cho phép Frontend tại `http://localhost:3659` gửi request, xử lý Preflight `OPTIONS`.
3. **Bảo toàn Header & Token**: Giữ nguyên header xác thực `Authorization: Bearer <JWT>`, `Content-Type`,... khi chuyển tiếp xuống backend.
4. **Chuẩn hóa lỗi hệ thống**: Trả về định dạng JSON thống nhất khi microservice đích bị sập (`502 Bad Gateway`) hoặc timeout (`504 Gateway Timeout`).
5. **Health Check Probe**: Cung cấp endpoint `GET /health` để giám sát trạng thái hoạt động của gateway.

---

## 2. Bảng Ánh Xạ Định Tuyến (Routing Table)

| Public Path qua Gateway (`:8877`) | Dịch Vụ Đích | URL Nội Bộ / Mặc Định | Mô Tả |
|:---|:---|:---|:---|
| `/api/accounts/*` | **Account Service** | `http://localhost:8661/api/accounts/*` | Đăng nhập, Profile, Số dư |
| `/api/tuitions/*` | **Tuition Service** | `http://localhost:8732/api/tuitions/*` | Tra cứu học phí, gạch nợ |
| `/api/payments/*` | **Payment Service** | `http://localhost:8815/api/payments/*` | Khởi tạo, xác nhận OTP, lịch sử |
| `/api/notifications/*` | **Notification Service** | `http://localhost:8940/api/notifications/*` | Sinh OTP, verify OTP, gửi mail |
| `/health` | **API Gateway** | Trực tiếp xử lý | Giám sát trạng thái hoạt động |

---

## 3. Cấu Trúc Thư Mục

```text
api-gateway/
├── Dockerfile                   # Container build specification
├── requirements.txt             # Dependencies: fastapi, uvicorn, httpx, pydantic-settings
├── .env.example                 # Mẫu URL các microservice
├── README.md                    # Tài liệu hướng dẫn này
│
└── app/
    ├── main.py                  # Khởi tạo FastAPI app, lifespan httpx.AsyncClient, định tuyến proxy /api/{service}/{path}
    │
    ├── config/
    │   └── env.py               # SERVICE_MAP và cấu hình URL các dịch vụ
    │
    ├── middlewares/
    │   ├── cors.py              # Cấu hình CORS middleware
    │   └── logging.py           # Log chi tiết thời gian xử lý và mã trạng thái
    │
    └── utils/
        └── forwarder.py         # Hàm forward_request: lọc hop-by-hop headers, proxy async
```

---

## 4. Cấu Hình Biến Môi Trường (`.env`)

Tạo file `.env` từ `.env.example`:
```ini
ACCOUNT_SERVICE_URL=http://localhost:8661
TUITION_SERVICE_URL=http://localhost:8732
PAYMENT_SERVICE_URL=http://localhost:8815
NOTIFICATION_SERVICE_URL=http://localhost:8940

ALLOWED_ORIGINS=http://localhost:3659,http://127.0.0.1:3659
```

---

## 5. Hướng Dẫn Chạy & Kiểm Thử

### 5.1 Cài đặt & Khởi chạy Gateway độc lập (Port 8877)
```bash
cd api-gateway
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8877 --reload
```

### 5.2 Kiểm thử định tuyến qua Gateway bằng cURL

#### 1. Kiểm tra Health Check:
```bash
curl -X GET http://localhost:8877/health
# Trả về: {"status":"ok","service":"api-gateway"}
```

#### 2. Test Proxy đến Account Service:
```bash
curl -X POST http://localhost:8877/api/accounts/login \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"sv.nguyen\", \"password\": \"Test@123\"}"
```

#### 3. Test Proxy đến Tuition Service:
```bash
curl -X GET http://localhost:8877/api/tuitions/students/521H0001
```

---

## 6. Bảng Kiểm Tra Nghiệm Thu (Checklist Cho Member 3)

- [ ] Định tuyến chính xác `/api/accounts/*` tới Account Service (:8661).
- [ ] Định tuyến chính xác `/api/tuitions/*` tới Tuition Service (:8732).
- [ ] Định tuyến chính xác `/api/payments/*` tới Payment Service (:8815).
- [ ] Định tuyến chính xác `/api/notifications/*` tới Notification Service (:8940).
- [ ] Xử lý CORS thành công cho Frontend Origin `http://localhost:3659`.
- [ ] Giữ nguyên Header `Authorization: Bearer ...` khi forward request.
- [ ] Trả về JSON chuẩn khi service con không phản hồi (`502` / `504`).
