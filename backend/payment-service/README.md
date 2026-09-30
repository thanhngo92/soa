# Payment Service — Tài Liệu Triển Khai Chi Tiết (Member 3)

> **Dự án:** iBanking Tuition Payment System (SOA)  
> **Người phụ trách:** **Member 3** (Payment Service Orchestrator + API Gateway + Frontend Integration)  
> **Công nghệ:** Python 3.11+ • FastAPI • HTTPX • aiomysql (MySQL 8.0)  
> **Port:** `8815` (Trực tiếp) | Qua Gateway: `http://localhost:8877/api/payments/...`  
> **Database:** `payment_db` (MySQL Port `8552`)

---

## 1. Mục Tiêu & Phạm Vi Công Việc (Member 3)

Payment Service là **Trung tâm điều phối Saga (Saga Orchestrator)** của toàn bộ hệ thống thanh toán học phí:
1. **Quản lý Cơ sở dữ liệu `payment_db`**: Lưu trữ các phiên thanh toán, trạng thái giao dịch (`PENDING`, `SUCCESS`, `FAILED`), và lịch sử thanh toán của từng tài khoản.
2. **Khởi tạo phiên thanh toán (`POST /initiate`)**: Kiểm tra trạng thái học phí từ Tuition Service, tạo bản ghi thanh toán, và yêu cầu Notification Service gửi mã OTP.
3. **Thực thi Saga Thanh toán & Bù trừ giao dịch (`POST /confirm`)**:
   * Xác thực mã OTP qua Notification Service.
   * **Bước 1:** Trừ tiền tài khoản người dùng qua Account Service (`/deduct`).
   * **Bước 2:** Gạch nợ học phí qua Tuition Service (`/pay`).
   * **Bù trừ (Compensation Rollback):** Nếu Bước 1 thành công nhưng Bước 2 thất bại (do học phí đã bị người khác thanh toán, lỗi mạng,...), lập tức gọi API hoàn tiền (`/refund`) bên Account Service và đánh dấu giao dịch `FAILED`.
4. **Truy vấn lịch sử giao dịch (`GET /history`)**: Cho phép người dùng xem lại danh sách các giao dịch đã thực hiện.

---

## 2. Luồng Điều Phối Saga Chi Tiết (Sequence Diagram)

```text
CLIENT (Frontend)       PAYMENT SERVICE           TUITION SERVICE       NOTIFICATION SERVICE      ACCOUNT SERVICE
      │                        │                         │                        │                      │
      ├──── POST /initiate ───>│                         │                        │                      │
      │                        ├─ GET /students/{mssv} ─>│                        │                      │
      │                        │<─ 200 OK (Invoice) ─────┤                        │                      │
      │                        ├─ INSERT payments (PENDING)                       │                      │
      │                        ├─ POST /otp/generate ────────────────────────────>│                      │
      │<── 200 {payment_id} ───┤                                                  ├─ (Send email OTP)    │
      │                        │                                                  │                      │
      │ (Nhập OTP & bấm xác nhận)                                                 │                      │
      ├──── POST /confirm ────>│                                                  │                      │
      │                        ├─ POST /otp/verify ──────────────────────────────>│                      │
      │                        │<─ 200 OK (OTP hợp lệ) ───────────────────────────┤                      │
      │                        │                                                                         │
      │                        ├────── Bước 1: POST /deduct (Trừ tiền tài khoản) ───────────────────────>│
      │                        │<───── 200 OK (Đã trừ tiền thành công) ──────────────────────────────────┤
      │                        │                                                                         │
      │                        ├────── Bước 2: POST /pay (Gạch nợ học phí) ──────>│                      │
      │                        │                                                  │                      │
      │           ┌────────────┴──────────────────────────────────────┐           │                      │
      │           │                                                   │           │                      │
      │       [Thành công]                                         [Thất bại]     │                      │
      │           │                                                   │           │                      │
      │           ├─ UPDATE status = 'SUCCESS'                        ├─ Bước bù trừ: POST /refund ─────>│
      │           ├─ POST /email/success ────> Notification           │<─ 200 OK (Đã hoàn lại tiền) ─────┤
      │<─ 200 OK ─┤                                                   ├─ UPDATE status = 'FAILED'        │
      │           │                                                   │<─ 409 Conflict ──────────────────┤
```

---

## 3. Cấu Trúc Thư Mục Chuẩn

```text
backend/payment-service/
├── Dockerfile                   # Container build specification
├── requirements.txt             # Dependencies: fastapi, uvicorn, aiomysql, httpx, pyjwt, pydantic-settings
├── .env.example                 # File mẫu biến môi trường
├── README.md                    # Tài liệu hướng dẫn này
│
└── app/
    ├── main.py                  # Khởi tạo FastAPI app, lifespan quản lý httpx.AsyncClient & DB pool
    │
    ├── config/
    │   ├── env.py               # Biến môi trường: DB URL, Downstream Service URLs, JWT Secret
    │   └── database.py          # Quản lý aiomysql connection pool
    │
    ├── routes/
    │   └── payment_routes.py    # Khai báo endpoint: /initiate, /confirm, /history
    │
    ├── middlewares/
    │   ├── auth_middleware.py   # Xác thực JWT Bearer token của client
    │   └── error_middleware.py  # Xử lý ngoại lệ toàn cục
    │
    ├── controllers/
    │   └── payment_controller.py# Nhận request, gọi service điều phối Saga, trả JSON chuẩn
    │
    ├── services/
    │   └── payment_service.py   # Trung tâm điều phối Saga (Initiate, Confirm, Compensation, History)
    │
    ├── clients/                 # Giao tiếp HTTP với các microservice khác
    │   ├── account_client.py    # Gọi Account Service: /deduct, /refund
    │   ├── tuition_client.py    # Gọi Tuition Service: /students/{mssv}, /pay
    │   └── notification_client.py# Gọi Notification Service: /otp/generate, /otp/verify, /email/success
    │
    ├── repositories/
    │   └── payment_repository.py# Thao tác bảng payments trong payment_db
    │
    ├── schemas/
    │   ├── payment_schema.py    # DTO: InitiatePaymentRequest, ConfirmPaymentRequest,...
    │   └── payment_document.py  # Mô tả cấu trúc bảng payments
    │
    └── utils/
        ├── response_util.py     # Chuẩn hóa JSON response
        └── error_util.py        # Custom AppError exception
```

---

## 4. Database Schema (`payment_db`)

### Cấu trúc bảng `payments`
```sql
CREATE DATABASE IF NOT EXISTS payment_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE payment_db;

CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    student_id VARCHAR(50) NOT NULL,
    student_name VARCHAR(255) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    error_code VARCHAR(50) NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Bảng Trạng Thái Nghiệp Vụ (`status`):
* `PENDING`: Đã tạo phiên thanh toán, đã gửi mã OTP, đang chờ người dùng nhập OTP.
* `SUCCESS`: Đã xác thực OTP, trừ tiền tài khoản thành công và gạch nợ học phí thành công.
* `FAILED`: Giao dịch thất bại (ví dụ: gạch nợ học phí thất bại $\rightarrow$ đã kích hoạt refund hoàn tiền thành công).

---

## 5. Đặc Tả Chi Tiết API Contract

### 5.1 Khởi tạo giao dịch thanh toán (`POST /api/payments/initiate`)
* **Mô tả:** Kiểm tra học phí của sinh viên, tạo bản ghi `PENDING`, gửi OTP qua email của tài khoản đăng nhập.
* **Headers:** `Authorization: Bearer <access_token>`
* **Request Body:**
```json
{
  "student_id": "521H0001"
}
```
* **Response 200 (Thành công):**
```json
{
  "success": true,
  "data": {
    "payment_id": "1",
    "amount": 4850000.0,
    "student_name": "Nguyen Van An"
  }
}
```
* **Response 409 (Học phí đã được thanh toán):**
```json
{
  "success": false,
  "error": {
    "code": "TUITION_ALREADY_PAID",
    "message": "Tuition has already been paid"
  }
}
```

---

### 5.2 Xác thực OTP và Hoàn tất thanh toán (`POST /api/payments/confirm`)
* **Mô tả:** Xác thực mã OTP $\rightarrow$ Trừ tiền tài khoản $\rightarrow$ Gạch nợ học phí $\rightarrow$ Tự động hoàn tiền (Refund) nếu gạch nợ thất bại.
* **Headers:** `Authorization: Bearer <access_token>`
* **Request Body:**
```json
{
  "payment_id": "1",
  "otp_code": "654321"
}
```
* **Response 200 (Thanh toán hoàn tất thành công):**
```json
{
  "success": true,
  "data": {
    "payment_id": "1",
    "status": "SUCCESS",
    "amount": 4850000.0,
    "student_id": "521H0001",
    "paid_at": "2026-09-30T10:00:00Z"
  }
}
```
* **Response 400 (Sai OTP / Hết hạn):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_OTP",
    "message": "OTP is invalid, expired, or already used"
  }
}
```
* **Response 409 (Saga Rollback: Học phí bị trùng $\rightarrow$ Đã hoàn tiền):**
```json
{
  "success": false,
  "error": {
    "code": "PAYMENT_FAILED",
    "message": "Payment failed: tuition already paid by another transaction"
  }
}
```

---

### 5.3 Lịch sử giao dịch của người dùng (`GET /api/payments/history`)
* **Mô tả:** Lấy danh sách toàn bộ các phiên thanh toán của tài khoản đang đăng nhập.
* **Headers:** `Authorization: Bearer <access_token>`
* **Response 200 (Thành công):**
```json
{
  "success": true,
  "data": [
    {
      "payment_id": "1",
      "student_id": "521H0001",
      "student_name": "Nguyen Van An",
      "amount": 4850000.0,
      "status": "SUCCESS",
      "created_at": "2026-09-30T10:00:00Z",
      "completed_at": "2026-09-30T10:01:00Z"
    }
  ]
}
```

---

## 6. Logic Bù Trừ Giao Dịch (Compensating Transaction)

Đoạn mã mẫu triển khai Saga trong `payment_service.py`:
```python
# 1. Trừ tiền số dư tài khoản
await account_client.deduct(http, token, amount, payment_id)

# 2. Gạch nợ học phí sinh viên
try:
    await tuition_client.pay(http, student_id, user["sub"], payment_id)
except AppError:
    # KÍCH HOẠT BÙ TRỪ GIAO DỊCH (ROLLBACK SAGA):
    await account_client.refund(http, token, amount, payment_id)
    await update_status(payment_id, "FAILED", "TUITION_MARK_FAILED")
    raise AppError("PAYMENT_FAILED", "Payment failed: tuition already paid by another transaction", 409)

# 3. Hoàn tất thành công
await update_status(payment_id, "SUCCESS")
```

---

## 7. Biến Môi Trường (`.env`)

Tạo file `.env` từ `.env.example`:
```ini
DB_HOST=localhost
DB_PORT=8552
DB_USER=root
DB_PASSWORD=rootpassword
DB_NAME=payment_db

ACCOUNT_SERVICE_URL=http://localhost:8661
TUITION_SERVICE_URL=http://localhost:8732
NOTIFICATION_SERVICE_URL=http://localhost:8940

JWT_SECRET=super-secret-key-for-ibanking-jwt-token-2024
```

---

## 8. Hướng Dẫn Chạy & Kiểm Thử Toàn Trình (E2E Test)

### 8.1 Cài đặt & Khởi chạy Service (Port 8815)
```bash
# 1. Di chuyển vào thư mục service
cd backend/payment-service

# 2. Tạo virtual environment & cài dependencies
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac
pip install -r requirements.txt

# 3. Khởi chạy service
uvicorn app.main:app --host 0.0.0.0 --port 8815 --reload
```

### 8.2 Kịch bản kiểm thử toàn trình (End-to-End Test):
1. **Đăng nhập:** Gọi Account Service `POST /api/accounts/login` lấy token của `sv.nguyen`.
2. **Khởi tạo Payment:**
   ```bash
   curl -X POST http://localhost:8815/api/payments/initiate \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d "{\"student_id\": \"521H0001\"}"
   ```
3. **Lấy mã OTP:** Mở Mailpit [http://localhost:8025](http://localhost:8025) để lấy mã 6 chữ số vừa gửi.
4. **Xác nhận Payment:**
   ```bash
   curl -X POST http://localhost:8815/api/payments/confirm \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d "{\"payment_id\": \"1\", \"otp_code\": \"<MA_OTP_MAILPIT>\"}"
   ```
5. **Kiểm tra kết quả:**
   * Số dư của `sv.nguyen` giảm từ 7,500,000 xuống 2,650,000 VND (`GET /me`).
   * Trạng thái học phí của `521H0001` chuyển thành `PAID` (`GET /students/521H0001`).
   * Mailpit nhận được email thông báo biên nhận thanh toán thành công.
   * `GET /api/payments/history` hiển thị giao dịch vừa hoàn tất với trạng thái `SUCCESS`.

---

## 9. Bảng Kiểm Tra Nghiệm Thu (Checklist Cho Member 3)

- [ ] Kết nối `payment_db` thành công qua connection pool `aiomysql`.
- [ ] `POST /initiate` tạo bản ghi `payments` trạng thái `PENDING` và gọi `notification-service` gửi OTP qua email.
- [ ] `POST /initiate` với học phí đã `PAID` trả về 409 `TUITION_ALREADY_PAID`.
- [ ] `POST /confirm` kiểm tra đúng mã OTP qua `notification-service`.
- [ ] `POST /confirm` gọi trừ tiền tài khoản qua `account-service`.
- [ ] `POST /confirm` gọi gạch nợ học phí qua `tuition-service`.
- [ ] **Saga Compensation hoạt động:** Khi gạch nợ lỗi $\rightarrow$ tự động gọi `/refund` hoàn tiền cho khách hàng và ghi nhận giao dịch `FAILED`.
- [ ] `GET /history` trả về danh sách lịch sử chính xác theo tài khoản đang đăng nhập.
