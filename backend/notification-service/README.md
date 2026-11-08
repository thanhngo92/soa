# Notification Service

Dịch vụ quản lý vòng đời mã xác thực OTP và gửi email thông báo qua SMTP (Mailpit) trong hệ thống iBanking Tuition Payment System.

* **Công nghệ:** Python 3.11, FastAPI, aiomysql (MySQL 8.0), smtplib, Mailpit
* **Port:** `8940` (Qua Gateway: `/api/notifications/...`)
* **Database:** `notification_db` (MySQL Port `8552`)
* **Mailpit SMTP:** `localhost:1025` | Web UI: `http://localhost:8025`

---

## 1. Phạm Vi Chức Năng

1. **Quản lý Cơ sở dữ liệu `notification_db`:** Lưu trữ mã OTP gắn với `payment_id`, thời hạn hiệu lực (`expires_at`), số lần thử (`attempts`) và trạng thái sử dụng (`is_used`).
2. **Sinh mã OTP 6 chữ số (`POST /otp/generate` — Internal Only):** Vô hiệu hóa mã OTP cũ của cùng `payment_id`, sinh mã 6 chữ số không trùng với các OTP đang hoạt động, thời hạn 5 phút, và gửi email kèm thông tin giao dịch (`#payment_id`, MSSV, họ tên, số tiền).
3. **Xác thực OTP nguyên tử (`POST /otp/verify` — Internal Only):** Sử dụng ACID Transaction và khóa dòng `SELECT ... FOR UPDATE` để kiểm tra thời hạn 5 phút, giới hạn tối đa 3 lần nhập sai và đánh dấu đã sử dụng (`is_used = TRUE`) đúng một lần.
4. **Gửi Email Biên nhận (`POST /email/success` — Internal Only):** Gửi email xác nhận thanh toán học phí thành công theo múi giờ GMT+7.

---

## 2. Database Schema (`notification_db`)

```sql
CREATE TABLE IF NOT EXISTS otps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id VARCHAR(50) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    attempts INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_payment_id (payment_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_verify_otp (payment_id, otp_code, is_used),
    CONSTRAINT chk_otp_attempts CHECK (attempts >= 0 AND attempts <= 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 3. Đặc Tả API Endpoints (Internal Only)

Yêu cầu Header: `X-Internal-Token: <INTERNAL_SERVICE_KEY>`

* **`POST /api/notifications/otp/generate`**
  * Request: `{"payment_id": "1", "email": "nguyen.van.an@student.tdtu.edu.vn", "student_id": "521H0001", "student_name": "Nguyen Van An", "amount": 4850000.0}`
  * Response `200`: `{"success": true, "data": {"status": "SENT"}, "message": "OTP sent"}`
* **`POST /api/notifications/otp/verify`**
  * Request: `{"payment_id": "1", "otp_code": "654321"}`
  * Response `200`: `{"success": true, "data": {"valid": true}, "message": "OTP verified"}`
  * Response `400`: `INVALID_OTP` | `OTP_EXPIRED` | `OTP_ALREADY_USED` | `OTP_MAX_ATTEMPTS_EXCEEDED`
* **`POST /api/notifications/email/success`**
  * Request: `{"email": "...", "payment_id": "1", "student_name": "...", "student_id": "521H0001", "amount": 4850000.0, "paid_at": "..."}`
  * Response `200`: `{"success": true, "data": {"status": "SENT"}, "message": "Email sent"}`
