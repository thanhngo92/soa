# Notification Service — Tài Liệu Triển Khai Chi Tiết (Member 2)

> **Dự án:** iBanking Tuition Payment System (SOA)  
> **Người phụ trách:** **Member 2** (Tuition Service & Notification Service)  
> **Công nghệ:** Python 3.11+ • FastAPI • aiomysql (MySQL 8.0) • smtplib • Mailpit  
> **Port:** `8940` (Trực tiếp) | Qua Gateway: `http://localhost:8877/api/notifications/...`  
> **Database:** `notification_db` (MySQL Port `8552`)  
> **Mailpit SMTP Server:** `localhost:1025` | Web UI: `http://localhost:8025`

---

## 1. Mục Tiêu & Phạm Vi Công Việc (Member 2)

Member 2 chịu trách nhiệm về dịch vụ sinh/xác thực OTP hai lớp và gửi email thông báo:
1. **Quản lý Cơ sở dữ liệu `notification_db`**: Lưu trữ lịch sử mã OTP, thời hạn hết hạn (`expires_at`), trạng thái sử dụng (`is_used`).
2. **Sinh mã OTP 6 chữ số (`POST /otp/generate`)**: Tạo mã ngẫu nhiên 6 chữ số, thời hạn hiệu lực **5 phút**, gửi email chứa OTP đến địa chỉ email của người dùng qua SMTP Mailpit.
3. **Xác thực OTP Nguyên tử & Chống Replay (`POST /otp/verify`)**: Chuyển trạng thái `is_used = TRUE` nguyên tử ở mức database để đảm bảo mỗi mã OTP chỉ được sử dụng đúng 1 lần duy nhất (Single-Use Token).
4. **Gửi Email Xác nhận Thành công (`POST /email/success`)**: Gửi email biên lai thanh toán thành công sau khi giao dịch hoàn tất.

---

## 2. Cấu Trúc Thư Mục Chuẩn

```text
backend/notification-service/
├── Dockerfile                   # Container build specification
├── requirements.txt             # Dependencies: fastapi, uvicorn, aiomysql, pydantic-settings
├── .env.example                 # File mẫu biến môi trường
├── README.md                    # Tài liệu hướng dẫn này
│
└── app/
    ├── main.py                  # Khởi tạo FastAPI app, quản lý lifespan kết nối MySQL
    │
    ├── config/
    │   ├── env.py               # Nạp cấu hình DB và SMTP (Host, Port, Mail From)
    │   └── database.py          # Quản lý aiomysql connection pool
    │
    ├── routes/
    │   └── notification_routes.py # Khai báo endpoint: /otp/generate, /otp/verify, /email/success
    │
    ├── middlewares/
    │   └── error_middleware.py  # Xử lý lỗi toàn cục
    │
    ├── controllers/
    │   └── notification_controller.py # Nhận DTO và trả về response chuẩn
    │
    ├── services/
    │   └── notification_service.py   # Logic sinh OTP, gửi mail qua smtplib, verify OTP
    │
    ├── repositories/
    │   └── notification_repository.py# Thao tác SQL (INSERT OTP, Atomic Verify UPDATE)
    │
    ├── schemas/
    │   └── notification_schema.py   # DTO: GenerateOtpRequest, VerifyOtpRequest,...
    │
    └── utils/
        ├── response_util.py     # Chuẩn hóa JSON response
        └── error_util.py        # Custom AppError exception
```

---

## 3. Database Schema (`notification_db`)

### Cấu trúc bảng `otps`
```sql
CREATE DATABASE IF NOT EXISTS notification_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE notification_db;

CREATE TABLE IF NOT EXISTS otps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id VARCHAR(50) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_payment_id (payment_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 4. Đặc Tả Chi Tiết API Contract

### 4.1 Sinh mã OTP (`POST /api/notifications/otp/generate`)
* **Mô tả:** Vô hiệu hóa mã OTP cũ của `payment_id` (nếu có), sinh mã OTP ngẫu nhiên 6 chữ số mới có hiệu lực 5 phút và gửi email qua Mailpit.
* **Request Body:**
```json
{
  "payment_id": "1",
  "email": "nguyen.van.an@student.tdtu.edu.vn"
}
```
* **Response 200 (Thành công):**
```json
{
  "success": true,
  "message": "OTP sent"
}
```

---

### 4.2 Xác thực mã OTP (`POST /api/notifications/otp/verify`)
* **Mô tả:** Kiểm tra mã OTP. Nếu hợp lệ, còn hạn và chưa dùng $\rightarrow$ đánh dấu `is_used = TRUE` nguyên tử.
* **Request Body:**
```json
{
  "payment_id": "1",
  "otp_code": "654321"
}
```
* **Response 200 (Hợp lệ):**
```json
{
  "success": true,
  "message": "OTP verified"
}
```
* **Response 400 (Sai mã / Hết hạn / Đã dùng):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_OTP",
    "message": "OTP is invalid, expired, or already used"
  }
}
```

---

### 4.3 Gửi email biên nhận thanh toán (`POST /api/notifications/email/success`)
* **Mô tả:** Gửi email thông báo thanh toán học phí thành công kèm thông tin chi tiết.
* **Request Body:**
```json
{
  "email": "nguyen.van.an@student.tdtu.edu.vn",
  "payment_id": "1",
  "student_name": "Nguyen Van An",
  "student_id": "521H0001",
  "amount": 4850000.0,
  "paid_at": "2026-09-30T10:00:00Z"
}
```
* **Response 200 (Thành công):**
```json
{
  "success": true,
  "message": "Email sent"
}
```

---

## 5. Quy Tắc Concurrency & Chống Tấn Công Replay OTP

> **Lưu ý quan trọng:**  
> **Tuyệt đối không SELECT OTP lên kiểm tra bằng code Python rồi mới UPDATE `is_used`.**  
> Việc xác thực và đánh dấu đã sử dụng phải diễn ra trong **1 câu lệnh SQL UPDATE Atomic DUY NHẤT**.

### Câu lệnh Atomic Verify trong `notification_repository.py`:
```sql
UPDATE otps 
SET is_used = TRUE 
WHERE payment_id = %s 
  AND otp_code = %s 
  AND is_used = FALSE 
  AND expires_at >= NOW();
```
* **Xử lý kết quả:**
  * `cursor.rowcount == 1`: Mã OTP hợp lệ, chưa từng sử dụng, còn trong thời hạn 5 phút $\rightarrow$ Xác thực thành công.
  * `cursor.rowcount == 0`: Mã OTP không đúng, HOẶC đã bị sử dụng trước đó (chống Replay Attack), HOẶC đã hết hạn quá 5 phút $\rightarrow$ Ném lỗi `INVALID_OTP` (HTTP 400).

---

## 6. Cấu Hình Biến Môi Trường & Mailpit

Tạo file `.env` từ `.env.example`:
```ini
DB_HOST=localhost
DB_PORT=8552
DB_USER=root
DB_PASSWORD=rootpassword
DB_NAME=notification_db

SMTP_HOST=localhost
SMTP_PORT=1025
MAIL_FROM=noreply@tdtu.edu.vn
```

---

## 7. Hướng Dẫn Chạy & Kiểm Thử Độc Lập

### 7.1 Cài đặt & Khởi chạy Service (Port 8940)
```bash
# 1. Di chuyển vào thư mục service
cd backend/notification-service

# 2. Tạo virtual environment & cài dependencies
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac
pip install -r requirements.txt

# 3. Khởi chạy service
uvicorn app.main:app --host 0.0.0.0 --port 8940 --reload
```

### 7.2 Kiểm thử bằng cURL

#### 1. Sinh mã OTP:
```bash
curl -X POST http://localhost:8940/api/notifications/otp/generate \
  -H "Content-Type: application/json" \
  -d "{\"payment_id\": \"TXN-001\", \"email\": \"student@example.com\"}"
```
* Mở trình duyệt truy cập Web Mailpit tại: [http://localhost:8025](http://localhost:8025) để xem email nhận mã OTP 6 số.

#### 2. Xác thực OTP thành công:
```bash
curl -X POST http://localhost:8940/api/notifications/otp/verify \
  -H "Content-Type: application/json" \
  -d "{\"payment_id\": \"TXN-001\", \"otp_code\": \"<MA_OTP_XEM_TRONG_MAILPIT>\"}"
```

#### 3. Thử xác thực lại OTP lần 2 (Kiểm tra chống Replay):
```bash
curl -X POST http://localhost:8940/api/notifications/otp/verify \
  -H "Content-Type: application/json" \
  -d "{\"payment_id\": \"TXN-001\", \"otp_code\": \"<MA_OTP_XEM_TRONG_MAILPIT>\"}"
```
*(Kết quả mong đợi: Trả về lỗi 400 `INVALID_OTP` vì mã đã được tiêu thụ ở bước 2)*

#### 4. Gửi email xác nhận thanh toán thành công:
```bash
curl -X POST http://localhost:8940/api/notifications/email/success \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"student@example.com\", \"payment_id\": \"TXN-001\", \"student_name\": \"Nguyen Van An\", \"student_id\": \"521H0001\", \"amount\": 4850000, \"paid_at\": \"2026-09-30T10:00:00\"}"
```

---

## 8. Bảng Kiểm Tra Nghiệm Thu (Checklist Cho Member 2)

- [ ] Kết nối `notification_db` thành công qua connection pool `aiomysql`.
- [ ] `POST /otp/generate` sinh đúng 6 chữ số, lưu vào bảng `otps` với `expires_at = NOW() + 5 phút`.
- [ ] Email gửi đến Mailpit hiển thị đúng tiêu đề, địa chỉ nhận và mã OTP.
- [ ] `POST /otp/verify` với OTP đúng trả về `200 OTP verified` và cập nhật `is_used = TRUE`.
- [ ] `POST /otp/verify` với OTP sai hoặc đã dùng bị từ chối với `400 INVALID_OTP`.
- [ ] `POST /email/success` gửi mail định dạng biên lai thanh toán đầy đủ thông tin tới Mailpit.
