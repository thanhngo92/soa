# Account Service

Dịch vụ quản lý tài khoản người dùng, xác thực JWT và sổ cái biến động số dư trong hệ thống iBanking Tuition Payment System.

* **Công nghệ:** Python 3.11, FastAPI, Bcrypt, PyJWT, aiomysql (MySQL 8.0)
* **Port:** `8661` (Qua Gateway: `/api/accounts/...`)
* **Database:** `account_db` (MySQL Port `8552`)

---

## 1. Phạm Vi Chức Năng

1. **Quản lý Cơ sở dữ liệu `account_db`:** Bao gồm bảng `accounts` (ràng buộc `balance >= 0`) và bảng sổ cái `account_transactions` (ràng buộc `UNIQUE (account_id, reference_id, transaction_type)`).
2. **Xác thực & Phân quyền:** Kiểm tra mật khẩu bằng Bcrypt, cấp phát JWT Bearer Token khi đăng nhập, xác thực người dùng qua JWT hoặc xác thực liên dịch vụ qua `X-Internal-Token`.
3. **Tra cứu thông tin (`/me`):** Truy xuất hồ sơ chủ tài khoản và số dư khả dụng.
4. **Trừ tiền nguyên tử (`/deduct`):** Thực thi trong ACID Transaction kết hợp khóa dòng `SELECT ... FOR UPDATE`, cập nhật điều kiện `balance >= amount` và ghi sổ cái `account_transactions`, đảm bảo không thấu chi và không trừ tiền đúp.
5. **Hoàn tiền bù trừ (`/refund`):** Thực thi giao dịch bù trừ (Compensating Transaction) có kiểm tra đối soát bút toán gốc `DEDUCT` khi nhận yêu cầu hoàn tiền từ Payment Service.

---

## 2. Cấu Trúc Thư Mục

```text
backend/account-service/
|-- Dockerfile
|-- requirements.txt
|-- .env.example
|-- README.md
|-- db/
|   +-- init.sql
+-- app/
    |-- main.py
    |-- config/
    |   |-- env.py
    |   +-- database.py
    |-- routes/
    |   +-- account_routes.py
    |-- middlewares/
    |   |-- auth_middleware.py
    |   +-- error_middleware.py
    |-- controllers/
    |   +-- account_controller.py
    |-- services/
    |   +-- account_service.py
    |-- repositories/
    |   +-- account_repository.py
    |-- schemas/
    |   +-- account_schema.py
    +-- utils/
        |-- response_util.py
        +-- error_util.py
```

---

## 3. Database Schema & Dữ Liệu Mẫu (`account_db`)

```sql
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_balance CHECK (balance >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS account_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    balance_before DECIMAL(15, 2) NOT NULL,
    balance_after DECIMAL(15, 2) NOT NULL,
    reference_id VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_account_tx (account_id, created_at DESC),
    INDEX idx_ref_id (reference_id),
    UNIQUE KEY uq_account_ref_type (account_id, reference_id, transaction_type),
    CONSTRAINT fk_tx_account FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_tx_amount CHECK (amount > 0),
    CONSTRAINT chk_tx_type CHECK (transaction_type IN ('DEDUCT', 'REFUND')),
    CONSTRAINT chk_tx_balance_math CHECK (
        (transaction_type = 'DEDUCT' AND balance_after = balance_before - amount AND balance_after >= 0)
        OR (transaction_type = 'REFUND' AND balance_after = balance_before + amount)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Dữ liệu mẫu
| ID | Username | Mật khẩu | Họ và Tên | Email | Số dư (VND) |
|:---|:---|:---|:---|:---|:---|
| `1` | `sv.nguyen` | `Test@123` | Nguyễn Văn An | `nguyen.van.an@student.tdtu.edu.vn` | 7,500,000 |
| `2` | `sv.tran` | `Test@123` | Trần Thị Bảo | `tran.thi.bao@student.tdtu.edu.vn` | 2,300,000 |
| `3` | `sv.le` | `Test@123` | Lê Hoàng Cường | `le.hoang.cuong@student.tdtu.edu.vn` | 12,000,000 |

---

## 4. Đặc Tả API Endpoints

* **`POST /api/accounts/login`**
  * Request: `{"username": "sv.nguyen", "password": "Test@123"}`
  * Response `200`: `{"success": true, "data": {"access_token": "<JWT>", "token_type": "bearer"}}`
* **`GET /api/accounts/me`**
  * Header: `Authorization: Bearer <access_token>`
  * Response `200`: `{"success": true, "data": {"id": "1", "username": "sv.nguyen", "full_name": "Nguyen Van An", "email": "nguyen.van.an@student.tdtu.edu.vn", "phone": "0901234567", "balance": 7500000.0}}`
* **`POST /api/accounts/deduct`** *(Internal Only)*
  * Header: `X-Internal-Token: <INTERNAL_SERVICE_KEY>`
  * Request: `{"account_id": "1", "amount": 4850000.0, "transaction_id": "1"}`
  * Response `200`: `{"success": true, "data": {"balance": 2650000.0}}`
* **`POST /api/accounts/refund`** *(Internal Only)*
  * Header: `X-Internal-Token: <INTERNAL_SERVICE_KEY>`
  * Request: `{"account_id": "1", "amount": 4850000.0, "transaction_id": "1"}`
  * Response `200`: `{"success": true, "data": {"balance": 7500000.0}}`
