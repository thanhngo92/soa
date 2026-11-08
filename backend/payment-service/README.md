# Payment Service

Dịch vụ điều phối giao dịch thanh toán học phí (Saga Orchestrator) trong hệ thống iBanking Tuition Payment System.

* **Công nghệ:** Python 3.11, FastAPI, HTTPX, aiomysql (MySQL 8.0)
* **Port:** `8815` (Qua Gateway: `/api/payments/...`)
* **Database:** `payment_db` (MySQL Port `8552`)

---

## 1. Phạm Vi Chức Năng

1. **Quản lý Cơ sở dữ liệu `payment_db` (Chuẩn 3NF):** Lưu trữ thông tin giao dịch gắn với `account_id (INT)` và `tuition_id (INT)`, số tiền (`amount`), trạng thái xử lý (`PENDING`, `PROCESSING`, `SUCCESS`, `FAILED`), mã lỗi (`error_code`) và dấu thời gian.
2. **Khởi tạo giao dịch (`POST /initiate`):** Kiểm tra công nợ học phí từ Tuition Service, đối chiếu số dư khả dụng từ Account Service, tạo bản ghi `PENDING` mới gắn với `tuition_id` và yêu cầu Notification Service gửi mã OTP qua email.
3. **Xác nhận OTP & Thực thi Saga (`POST /confirm`):**
   * Xác thực mã OTP qua Notification Service (nếu OTP hết hạn hoặc nhập sai quá 3 lần thì chuyển trạng thái giao dịch sang `FAILED`).
   * Chuyển trạng thái nguyên tử từ `PENDING` sang `PROCESSING` bằng khóa dòng `SELECT ... FOR UPDATE`.
   * Bước 1: Trừ số dư tài khoản tại Account Service (`/deduct`).
   * Bước 2: Gạch nợ học phí theo `tuition_id` tại Tuition Service (`/pay`).
   * Bù trừ (Saga Compensation): Nếu Bước 1 thành công nhưng Bước 2 thất bại, gọi ngay `/refund` tại Account Service để hoàn tiền cho người dùng và cập nhật trạng thái giao dịch sang `FAILED` (`TUITION_MARK_FAILED`).
4. **Truy vấn lịch sử (`GET /history`):** Trả về danh sách lịch sử các giao dịch thanh toán thành công (`SUCCESS`) của người dùng.

---

## 2. Database Schema (`payment_db`)

```sql
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    tuition_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    error_code VARCHAR(50) NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    INDEX idx_tuition_id (tuition_id),
    INDEX idx_account_created (account_id, created_at DESC),
    CONSTRAINT chk_payment_amount CHECK (amount > 0),
    CONSTRAINT chk_payment_status CHECK (status IN ('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 3. Cấu Hình Biến Môi Trường (`.env`)

```ini
SERVICE_NAME=payment-service
PORT=8815
MYSQL_HOST=localhost
MYSQL_PORT=8552
MYSQL_USER=root
MYSQL_PASSWORD=rootpassword
MYSQL_DATABASE=payment_db
JWT_SECRET=super_secret_jwt_key_change_in_prod
INTERNAL_SERVICE_KEY=super_internal_service_secret_key_2026
ACCOUNT_SERVICE_URL=http://account-service:8661
TUITION_SERVICE_URL=http://tuition-service:8732
NOTIFICATION_SERVICE_URL=http://notification-service:8940
```
