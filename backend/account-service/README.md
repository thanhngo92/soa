# Account Service — Tài Liệu Triển Khai Chi Tiết (Member 1)

> **Dự án:** iBanking Tuition Payment System (SOA)  
> **Người phụ trách:** **Member 1** (Account Service + DB Baseline + Authentication)  
> **Công nghệ:** Python 3.11+ • FastAPI • Bcrypt • PyJWT • aiomysql (MySQL 8.0)  
> **Port:** `8661` (Trực tiếp) | Qua Gateway: `http://localhost:8877/api/accounts/...`  
> **Database:** `account_db` (MySQL Port `8552`)

---

## 1. Mục Tiêu & Phạm Vi Công Việc (Member 1)

Member 1 chịu trách nhiệm toàn bộ về quản lý tài khoản người dùng và xác thực bảo mật:
1. **Quản lý Cơ sở dữ liệu `account_db`**: Tạo bảng, ràng buộc số dư `>= 0`, khởi tạo seed data mẫu.
2. **Xác thực & Phân quyền**: Băm mật khẩu bằng Bcrypt, cấp phát JWT Bearer Token khi đăng nhập, middleware giải mã token.
3. **Tra cứu thông tin (`/me`)**: Lấy thông tin cá nhân và số dư khả dụng của tài khoản đăng nhập.
4. **Trừ tiền Atomic (`/deduct`)**: Kiểm soát đồng thời bằng câu lệnh SQL điều kiện nguyên tử, chống race condition khi có nhiều giao dịch cùng lúc.
5. **Hoàn tiền Bù trừ (`/refund`)**: Cung cấp API bù trừ (Compensating Transaction) cho Saga khi Payment Service yêu cầu hoàn tiền.

---

## 2. Cấu Trúc Thư Mục Chuẩn

```text
backend/account-service/
├── Dockerfile                   # Build image container
├── requirements.txt             # Thư viện: fastapi, uvicorn, aiomysql, bcrypt, pyjwt, pydantic-settings
├── .env.example                 # Mẫu cấu hình môi trường
├── README.md                    # Tài liệu hướng dẫn này
│
└── app/
    ├── main.py                  # Khởi tạo FastAPI app, lifespan quản lý pool DB, đăng ký routes
    │
    ├── config/
    │   ├── env.py               # Đọc biến môi trường (DB host/user/pass/port, JWT secret, expiry)
    │   └── database.py          # Quản lý aiomysql connection pool
    │
    ├── routes/
    │   └── account_routes.py    # Định nghĩa endpoint: /login, /me, /deduct, /refund
    │
    ├── middlewares/
    │   ├── auth_middleware.py   # Xác thực JWT Bearer Token, trích xuất user context
    │   └── error_middleware.py  # Xử lý lỗi toàn cục (Global Exception Handler)
    │
    ├── controllers/
    │   └── account_controller.py# Tiếp nhận Request DTO, gọi Service, trả response chuẩn
    │
    ├── services/
    │   └── account_service.py   # Nghiệp vụ: login, profile, deduct, refund
    │
    ├── repositories/
    │   └── account_repository.py# Thao tác SQL với MySQL (Atomic UPDATE, SELECT)
    │
    ├── schemas/
    │   └── account_schema.py    # Pydantic DTO (LoginRequest, DeductRequest, RefundRequest,...)
    │
    └── utils/
        ├── response_util.py     # Chuẩn hóa JSON: {"success": true, "data": ...}
        └── error_util.py        # Custom Exception: AppError(code, message, status_code)
```

---

## 3. Database Schema & Seed Data (`account_db`)

### 3.1 Cấu trúc bảng `accounts`
```sql
CREATE DATABASE IF NOT EXISTS account_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE account_db;

CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_balance CHECK (balance >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3.2 Dữ liệu mẫu (Seed Data)
Dữ liệu đã được nạp sẵn qua `init-db/init-mysql.sql`:
| ID | Username | Password gốc | Full Name | Email | Số dư (VND) |
|:---|:---|:---|:---|:---|:---|
| `1` | `user01` | `Test@123` | Nguyen Van An | `nguyen.van.an@student.tdtu.edu.vn` | **7,500,000** |
| `2` | `user02` | `Test@123` | Tran Thi Bao | `tran.thi.bao@student.tdtu.edu.vn` | **2,300,000** |
| `3` | `user03` | `Test@123` | Le Hoang Cuong | `le.hoang.cuong@student.tdtu.edu.vn` | **12,000,000** |

> *Ghi chú băm Bcrypt mẫu:* `Test@123` $\rightarrow$ `$2b$12$kEJGg8fVLyvUhWg2zsBY1ejZ.KFf1oRRPgrbTgOJmwUye9/50vcUi`

---

## 4. Đặc Tả Chi Tiết API Contract

Tất cả response đều tuân theo định dạng chuẩn:
* **Thành công:** `{"success": true, "data": { ... }}`
* **Thất bại:** `{"success": false, "error": {"code": "...", "message": "..."}}`

---

### 4.1 Đăng nhập iBanking (`POST /api/accounts/login`)
* **Mô tả:** Xác thực username và mật khẩu, trả về JWT Access Token.
* **Public:** Có (Không cần token).
* **Request Body:**
```json
{
  "username": "user01",
  "password": "Test@123"
}
```
* **Response 200 (Thành công):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```
* **JWT Payload Claim bắt buộc:**
```json
{
  "sub": "1",
  "username": "user01",
  "email": "nguyen.van.an@student.tdtu.edu.vn",
  "exp": 1759240000
}
```
* **Response 401 (Sai thông tin):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
  }
}
```

---

### 4.2 Lấy thông tin tài khoản (`GET /api/accounts/me`)
* **Mô tả:** Lấy thông tin cá nhân và số dư của tài khoản hiện tại.
* **Headers:** `Authorization: Bearer <access_token>`
* **Response 200 (Thành công):**
```json
{
  "success": true,
  "data": {
    "id": "1",
    "username": "user01",
    "full_name": "Nguyen Van An",
    "email": "nguyen.van.an@student.tdtu.edu.vn",
    "phone": "0901234567",
    "balance": 7500000.0
  }
}
```
* **Response 401 (Chưa đăng nhập / Token hết hạn):**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token"
  }
}
```

---

### 4.3 Trừ số dư tài khoản (`POST /api/accounts/deduct`)
* **Mô tả:** Trừ tiền trong tài khoản bằng atomic update. Phục vụ bước 1 trong Saga của Payment Service.
* **Headers:** `Authorization: Bearer <access_token>`
* **Request Body:**
```json
{
  "amount": 4850000.0
}
```
* **Response 200 (Thành công):**
```json
{
  "success": true,
  "data": {
    "balance": 2650000.0
  }
}
```
* **Response 400 (Số dư không đủ):**
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Insufficient balance"
  }
}
```

---

### 4.4 Hoàn tiền số dư (`POST /api/accounts/refund`)
* **Mô tả:** Cộng lại số tiền đã trừ (Compensating Transaction) khi bước gạch nợ học phí ở Tuition Service bị lỗi.
* **Headers:** `Authorization: Bearer <access_token>`
* **Request Body:**
```json
{
  "amount": 4850000.0
}
```
* **Response 200 (Thành công):**
```json
{
  "success": true,
  "data": {
    "balance": 7500000.0
  }
}
```

---

## 5. Quy Tắc Concurrency & Atomic Update Bắt Buộc

> **Lưu ý quan trọng:**  
> **Tuyệt đối KHÔNG sử dụng pattern `SELECT balance` sau đó tính toán trong code Python rồi mới `UPDATE balance`.**  
> Việc này sẽ gây lỗi Race Condition khi có 2 giao dịch đến cùng thời điểm.

### Câu lệnh Atomic Deduct tại `account_repository.py`:
```sql
UPDATE accounts 
SET balance = balance - %s 
WHERE id = %s AND balance >= %s;
```
* **Kiểm tra kết quả:**
  * Nếu `cursor.rowcount == 1`: Trừ tiền thành công, trả về số dư mới.
  * Nếu `cursor.rowcount == 0`: Số dư không đủ hoặc tài khoản không hợp lệ $\rightarrow$ Ném lỗi `INSUFFICIENT_BALANCE` (HTTP 400).

---

## 6. Biến Môi Trường (`.env`)

Tạo file `.env` từ `.env.example`:
```ini
DB_HOST=localhost
DB_PORT=8552
DB_USER=root
DB_PASSWORD=rootpassword
DB_NAME=account_db

JWT_SECRET=super-secret-key-for-ibanking-jwt-token-2024
JWT_EXPIRE_MINUTES=60
```

---

## 7. Hướng Dẫn Chạy & Kiểm Thử Độc Lập

### 7.1 Cài đặt và Chạy Service cục bộ (Port 8661)
```bash
# 1. Di chuyển vào thư mục service
cd backend/account-service

# 2. Tạo virtual environment & cài dependencies
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac
pip install -r requirements.txt

# 3. Khởi chạy service
uvicorn app.main:app --host 0.0.0.0 --port 8661 --reload
```

### 7.2 Kiểm thử bằng cURL

#### 1. Đăng nhập lấy Token:
```bash
curl -X POST http://localhost:8661/api/accounts/login \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"user01\", \"password\": \"Test@123\"}"
```

#### 2. Lấy Profile & Số dư:
```bash
curl -X GET http://localhost:8661/api/accounts/me \
  -H "Authorization: Bearer <TOKEN_O_BUOC_1>"
```

#### 3. Trừ tiền tài khoản:
```bash
curl -X POST http://localhost:8661/api/accounts/deduct \
  -H "Authorization: Bearer <TOKEN_O_BUOC_1>" \
  -H "Content-Type: application/json" \
  -d "{\"amount\": 1000000}"
```

#### 4. Hoàn tiền:
```bash
curl -X POST http://localhost:8661/api/accounts/refund \
  -H "Authorization: Bearer <TOKEN_O_BUOC_1>" \
  -H "Content-Type: application/json" \
  -d "{\"amount\": 1000000}"
```

---

## 8. Bảng Kiểm Tra Nghiệm Thu (Checklist Cho Member 1)

- [ ] Kết nối `account_db` thành công qua connection pool `aiomysql`.
- [ ] Login đúng pass $\rightarrow$ 200 + JWT Token (HS256).
- [ ] Login sai pass $\rightarrow$ 401 `INVALID_CREDENTIALS`.
- [ ] `GET /me` có token $\rightarrow$ 200 + đầy đủ username, full_name, email, phone, balance.
- [ ] `GET /me` không có token hoặc token sai $\rightarrow$ 401.
- [ ] Trừ tiền khi số dư đủ $\rightarrow$ 200 + balance giảm chính xác.
- [ ] Trừ tiền khi số dư không đủ $\rightarrow$ 400 `INSUFFICIENT_BALANCE`.
- [ ] Câu lệnh trừ tiền dùng Atomic `UPDATE ... WHERE balance >= amount`.
- [ ] `POST /refund` hoàn lại tiền chính xác.
