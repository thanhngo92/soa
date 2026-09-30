# Backend Microservices — Kiến Trúc & Hướng Dẫn Phát Triển

> **Hệ thống:** iBanking Tuition Payment System (SOA)  
> **Nhóm thực hiện:** 3 Thành viên  
> **Công nghệ cốt lõi:** Python 3.11+ • FastAPI • MySQL 8.0 (aiomysql) • HTTPX • Mailpit

---

## 1. Phân Chia Công Việc 3 Thành Viên (Team Member Assignment)

| Thành Viên | Dịch Vụ Phụ Trách | Database | Tài Liệu Hướng Dẫn Chi Tiết | Trách Nhiệm Chính |
|:---|:---|:---|:---|:---|
| **Member 1** | **`account-service`** | `account_db` | [account-service/README.md](file:///d:/TDTU/KTHDV/GK/soa/backend/account-service/README.md) | Quản lý tài khoản, Bcrypt, JWT auth, `/me`, Trừ tiền atomic, Hoàn tiền refund, Seed dữ liệu tài khoản. |
| **Member 2** | **`tuition-service`**<br>**`notification-service`** | `tuition_db`<br>`notification_db` | [tuition-service/README.md](file:///d:/TDTU/KTHDV/GK/soa/backend/tuition-service/README.md)<br>[notification-service/README.md](file:///d:/TDTU/KTHDV/GK/soa/backend/notification-service/README.md) | Tra cứu học phí theo MSSV, Gạch nợ atomic, Sinh mã OTP 6 số (TTL 5 phút), Xác thực OTP chống Replay, Gửi email qua Mailpit. |
| **Member 3** | **`payment-service`**<br>`api-gateway`<br>`frontend` | `payment_db` | [payment-service/README.md](file:///d:/TDTU/KTHDV/GK/soa/backend/payment-service/README.md)<br>[api-gateway/README.md](file:///d:/TDTU/KTHDV/GK/soa/api-gateway/README.md)<br>[frontend/README.md](file:///d:/TDTU/KTHDV/GK/soa/frontend/README.md) | Điều phối Saga Orchestrator (Initiate, Confirm, Bù trừ Refund), Định tuyến Gateway, Tích hợp giao diện Frontend, E2E Testing. |

---

## 2. Bảng Danh Mục Service & Network Ports

```text
Frontend :3659
   │
   ▼
API Gateway :8877
   ├── Account Service :8661 ────── account_db (MySQL :8552)
   ├── Tuition Service :8732 ────── tuition_db (MySQL :8552)
   ├── Payment Service :8815 ────── payment_db (MySQL :8552)
   └── Notification Service :8940 ── notification_db (MySQL :8552)
                                   Mailpit SMTP :1025 / Web :8025
```

| Component | Port | Công nghệ | Database | Chức năng chính |
|:---|:---|:---|:---|:---|
| **`account-service`** | `8661` | FastAPI, Bcrypt, PyJWT | `account_db` | Auth, Account Profile, Balance Deduct/Refund |
| **`tuition-service`** | `8732` | FastAPI, aiomysql | `tuition_db` | Tra cứu học phí MSSV, Gạch nợ hóa đơn |
| **`notification-service`**| `8940` | FastAPI, smtplib | `notification_db` | Sinh OTP 6 số (5 phút), Xác thực chống replay, Mailpit |
| **`payment-service`** | `8815` | FastAPI, HTTPX | `payment_db` | **Saga Orchestrator**, Điều phối thanh toán & Rollback |

---

## 3. Cấu Trúc Khung Chuẩn Từng Microservice (Uniform Skeleton)

Mọi microservice trong thư mục `backend/` đều tuân theo kiến trúc phân lớp nhất quán:

```text
backend/{service-name}/
├── Dockerfile                   # Cấu hình container Docker
├── requirements.txt             # Danh sách dependencies
├── .env.example                 # Mẫu biến môi trường
├── README.md                    # Tài liệu chi tiết của service
│
└── app/
    ├── main.py                  # Entrypoint, lifespan (khởi tạo DB pool / HTTP client), route
    │
    ├── config/
    │   ├── env.py               # Pydantic Settings đọc biến môi trường
    │   └── database.py          # aiomysql async connection pool
    │
    ├── routes/                  # Định nghĩa endpoints URL & HTTP methods
    ├── middlewares/             # Auth JWT guard & Global Exception Handler
    ├── controllers/             # Tiếp nhận request DTO, gọi service, trả response chuẩn
    ├── services/                # Logic nghiệp vụ, tính toán, điều phối
    ├── repositories/            # Thao tác SQL trực tiếp (Atomic updates, SELECT)
    ├── schemas/                 # Pydantic Request/Response DTOs & Table schemas
    ├── utils/                   # Chuẩn hóa Response JSON & Custom Exceptions
    └── clients/                 # HTTP client gọi các service khác (Dành cho payment-service)
```

---

## 4. Luồng Chuyển Giao Dữ Liệu (Layer Data Flow)

```text
Route ──> Middleware ──> Controller ──> Service ──> Repository ──> Database
```

* **`Route`**: Khai báo URI endpoint, phương thức HTTP, gắn controller tương ứng.
* **`Middleware`**: Xác thực token JWT, bảo vệ route, bắt ngoại lệ toàn cục.
* **`Controller`**: Nhận input đã validate từ Pydantic DTO, gọi Service và wrap output qua `response_util.py`.
* **`Service`**: Chứa toàn bộ nghiệp vụ, điều kiện kinh doanh, điều phối Saga. Hoàn toàn không phụ thuộc vào `Request`/`Response` của web framework.
* **`Repository`**: Độc quyền thực thi các câu lệnh SQL với MySQL qua `aiomysql`. Tuyệt đối không chứa logic tính toán.

---

## 5. Nguyên Tắc Kỹ Thuật Bắt Buộc

### 5.1 Cô lập Cơ sở dữ liệu (Database Isolation)
* Mỗi service **CHỈ** được truy cập database riêng của mình.
* **Không** tạo Foreign Key xuyên database.
* Mọi giao tiếp trao đổi dữ liệu giữa các nghiệp vụ khác nhau **BẮT BUỘC** thông qua REST API qua mạng nội bộ.

### 5.2 Kiểm soát đồng thời bằng Atomic Conditional Update
* **Trừ số dư tài khoản:**
  ```sql
  UPDATE accounts SET balance = balance - %s WHERE id = %s AND balance >= %s;
  ```
* **Gạch nợ học phí:**
  ```sql
  UPDATE tuitions SET status = 'PAID', paid_at = NOW(), paid_by = %s, transaction_id = %s WHERE student_id = %s AND status = 'UNPAID';
  ```
* **Xác thực OTP chống Replay:**
  ```sql
  UPDATE otps SET is_used = TRUE WHERE payment_id = %s AND otp_code = %s AND is_used = FALSE AND expires_at >= NOW();
  ```

### 5.3 Bù trừ giao dịch Saga (Compensating Transaction)
* Khi `payment-service` gọi `account-service` trừ tiền thành công, nhưng bước gạch nợ ở `tuition-service` thất bại:
  * `payment-service` **bắt buộc gọi ngay** `POST /api/accounts/refund` để hoàn tiền về tài khoản người dùng.
  * Cập nhật trạng thái giao dịch trong `payment_db` thành `FAILED` kèm lý do lỗi.

### 5.4 Chuẩn hóa Response JSON
Mọi endpoint trả về định dạng thống nhất:
* **Thành công:**
  ```json
  {"success": true, "data": { ... }}
  ```
* **Thất bại:**
  ```json
  {"success": false, "error": {"code": "ERROR_CODE", "message": "Chi tiết lỗi"}}
  ```

---

## 6. Hướng Dẫn Khởi Chạy Toàn Bộ Backend

```bash
# Di chuyển về thư mục gốc dự án
cd ..

# Khởi động toàn bộ MySQL, Mailpit, API Gateway và 4 Microservices
docker compose up --build -d
```
