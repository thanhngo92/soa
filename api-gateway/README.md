# API Gateway

Cổng giao tiếp tập trung (Single Entry Point) cho hệ thống iBanking Tuition Payment System, phát triển bằng Python 3.11, FastAPI và HTTPX.

* **Port công khai:** `8877`
* **Frontend Origin (CORS):** `http://localhost:3000`

---

## 1. Chức Năng Chính

1. **Định tuyến ngược (Reverse Proxy):** Tiếp nhận request từ Frontend và chuyển tiếp đến microservice đích theo tiền tố đường dẫn `/api/{service}/{path}`.
2. **Quản lý CORS:** Xử lý cấu hình Cross-Origin Resource Sharing tập trung cho ứng dụng web tại cổng `3000`.
3. **Workflow Guard:** Chặn các truy cập trực tiếp từ bên ngoài vào các endpoint nội bộ (`/api/tuitions/pay`, `/api/accounts/deduct`, `/api/accounts/refund`, `/api/notifications/otp/*`, `/api/notifications/email/success`) và loại bỏ header `X-Internal-Token` giả mạo từ client.
4. **Idempotency-Key Middleware:** Hỗ trợ header `Idempotency-Key` trên các phương thức thay đổi dữ liệu (`POST`, `PUT`, `PATCH`, `DELETE`) với TTL 5 phút để chống xử lý trùng lặp khi mạng chập chờn hoặc người dùng bấm đúp.
5. **Health Check tổng hợp (`GET /health`):** Kiểm tra trạng thái hoạt động của Gateway cùng toàn bộ 4 microservice phía sau.

---

## 2. Bảng Ánh Xạ Định Tuyến

| Đường dẫn qua Gateway (`:8877`) | Dịch vụ đích | URL nội bộ mặc định |
|:---|:---|:---|
| `/api/accounts/*` | Account Service | `http://account-service:8661/api/accounts/*` |
| `/api/tuitions/*` | Tuition Service | `http://tuition-service:8732/api/tuitions/*` |
| `/api/payments/*` | Payment Service | `http://payment-service:8815/api/payments/*` |
| `/api/notifications/*` | Notification Service | `http://notification-service:8940/api/notifications/*` |
| `/health` | API Gateway | Xử lý trực tiếp và thăm dò `/health` của 4 service |

---

## 3. Cấu Trúc Thư Mục

```text
api-gateway/
|-- Dockerfile
|-- requirements.txt
|-- .env.example
|-- README.md
+-- app/
    |-- main.py                  # Khởi tạo FastAPI, định tuyến proxy, Workflow Guard & Idempotency
    |-- config/
    |   +-- env.py               # Cấu hình SERVICE_MAP và ALLOWED_ORIGIN
    |-- middlewares/
    |   |-- cors.py              # Cấu hình CORS middleware
    |   |-- idempotency.py       # Quản lý bộ nhớ đệm Idempotency-Key
    |   +-- logging.py           # Ghi log thời gian xử lý và mã trạng thái HTTP
    +-- utils/
        +-- forwarder.py         # Chuyển tiếp request bất đồng bộ và lọc hop-by-hop headers
```

---

## 4. Cấu Hình Biến Môi Trường (`.env`)

```ini
ACCOUNT_SERVICE_URL=http://account-service:8661
TUITION_SERVICE_URL=http://tuition-service:8732
PAYMENT_SERVICE_URL=http://payment-service:8815
NOTIFICATION_SERVICE_URL=http://notification-service:8940
ALLOWED_ORIGIN=http://localhost:3000,http://127.0.0.1:3000
```

---

## 5. Khởi Chạy Độc Lập

```bash
cd api-gateway
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8877 --reload
```
