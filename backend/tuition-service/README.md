# Tuition Service — Tài Liệu Triển Khai Chi Tiết (Member 2)

> **Dự án:** iBanking Tuition Payment System (SOA)  
> **Người phụ trách:** **Member 2** (Tuition Service & Notification Service)  
> **Công nghệ:** Python 3.11+ • FastAPI • aiomysql (MySQL 8.0) • Pydantic v2  
> **Port:** `8732` (Trực tiếp) | Qua Gateway: `http://localhost:8877/api/tuitions/...`  
> **Database:** `tuition_db` (MySQL Port `8552`)

---

## 1. Mục Tiêu & Phạm Vi Công Việc (Member 2)

Member 2 chịu trách nhiệm về dịch vụ quản lý hóa đơn học phí của sinh viên:
1. **Quản lý Cơ sở dữ liệu `tuition_db`**: Tạo bảng `tuitions`, lưu trữ thông tin sinh viên, học kỳ, số tiền nợ học phí và trạng thái thanh toán (`UNPAID` / `PAID`).
2. **Tra cứu hóa đơn học phí (`GET /students/{mssv}`)**: Cho phép sinh viên/người dùng tra cứu thông tin học phí theo Mã Số Sinh Viên (MSSV).
3. **Gạch nợ Atomic (`POST /pay`)**: Thực hiện chuyển đổi trạng thái hóa đơn từ `UNPAID` sang `PAID` bằng **Atomic Conditional Update** ở mức cơ sở dữ liệu để chống double-spending/race conditions khi có nhiều phiên thanh toán đồng thời.
4. **Bù trừ giao dịch (`POST /revert`)**: Cho phép hoàn tác trạng thái từ `PAID` về `UNPAID` (theo đúng `transaction_id`) khi cần bù trừ trong Saga.

---

## 2. Cấu Trúc Thư Mục Chuẩn

```text
backend/tuition-service/
├── Dockerfile                   # Container build specification
├── requirements.txt             # Dependencies: fastapi, uvicorn, aiomysql, pydantic-settings
├── .env.example                 # File mẫu biến môi trường
├── README.md                    # Tài liệu hướng dẫn này
│
└── app/
    ├── main.py                  # Khởi tạo FastAPI app, quản lý lifespan kết nối MySQL
    │
    ├── config/
    │   ├── env.py               # Nạp biến môi trường cấu hình DB
    │   └── database.py          # Quản lý aiomysql connection pool
    │
    ├── routes/
    │   └── tuition_routes.py    # Khai báo endpoints: /students/{mssv}, /pay, /revert
    │
    ├── middlewares/
    │   └── error_middleware.py  # Xử lý lỗi toàn cục
    │
    ├── controllers/
    │   └── tuition_controller.py# Xử lý tham số và trả về response chuẩn
    │
    ├── services/
    │   └── tuition_service.py   # Logic nghiệp vụ: tra cứu, gạch nợ, revert
    │
    ├── repositories/
    │   └── tuition_repository.py# Thao tác SQL (Atomic UPDATE, SELECT)
    │
    ├── schemas/
    │   ├── tuition_schema.py    # DTO: PayTuitionRequest, RevertTuitionRequest,...
    │   └── tuition_document.py  # Mô tả schema bảng tuitions
    │
    └── utils/
        ├── response_util.py     # Chuẩn hóa JSON response
        └── error_util.py        # Custom AppError exception
```

---

## 3. Database Schema & Seed Data (`tuition_db`)

### 3.1 Cấu trúc bảng `tuitions`
```sql
CREATE DATABASE IF NOT EXISTS tuition_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tuition_db;

CREATE TABLE IF NOT EXISTS tuitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL UNIQUE,
    student_name VARCHAR(255) NOT NULL,
    major VARCHAR(255) NOT NULL,
    semester VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UNPAID',
    paid_at TIMESTAMP NULL DEFAULT NULL,
    paid_by VARCHAR(50) NULL DEFAULT NULL,
    transaction_id VARCHAR(100) NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3.2 Dữ liệu mẫu (Seed Data)
Dữ liệu được nạp sẵn qua `init-db/init-mysql.sql`:
| MSSV (`student_id`) | Họ và Tên | Ngành | Học kỳ | Học phí (VND) | Trạng thái |
|:---|:---|:---|:---|:---|:---|
| `521H0001` | Nguyen Van An | Cong nghe Thong tin | HK1/2024-2025 | **4,850,000** | `UNPAID` |
| `521H0002` | Tran Thi Bao | Ke toan | HK1/2024-2025 | **3,620,000** | `UNPAID` |
| `521H0003` | Le Hoang Cuong | Ky thuat Dien tu | HK1/2024-2025 | **5,130,000** | `UNPAID` |
| `522H0017` | Pham Duc Dung | Quan tri Kinh doanh | HK1/2024-2025 | **3,975,000** | `UNPAID` |
| `522H0041` | Hoang Thi Yen | Ngon ngu Anh | HK1/2024-2025 | **3,280,000** | `UNPAID` |
| `523H0089` | Vo Minh Khoa | Cong nghe Thong tin | HK1/2024-2025 | **4,720,000** | `UNPAID` |

---

## 4. Đặc Tả Chi Tiết API Contract

### 4.1 Tra cứu học phí sinh viên (`GET /api/tuitions/students/{mssv}`)
* **Mô tả:** Tra cứu thông tin học phí của một sinh viên theo MSSV.
* **Quyền hạn:** Public (Không yêu cầu JWT).
* **Response 200 (Tìm thấy):**
```json
{
  "success": true,
  "data": {
    "student_id": "521H0001",
    "student_name": "Nguyen Van An",
    "major": "Cong nghe Thong tin",
    "semester": "HK1/2024-2025",
    "amount": 4850000.0,
    "status": "UNPAID"
  }
}
```
* **Response 404 (Không tìm thấy sinh viên):**
```json
{
  "success": false,
  "error": {
    "code": "STUDENT_NOT_FOUND",
    "message": "Student 999H9999 not found"
  }
}
```

---

### 4.2 Gạch nợ học phí (`POST /api/tuitions/pay`)
* **Mô tả:** Chuyển trạng thái học phí sang `PAID` bằng câu lệnh SQL Atomic. Được gọi bởi `payment-service` trong bước 2 của Saga.
* **Request Body:**
```json
{
  "student_id": "521H0001",
  "paid_by": "1",
  "transaction_id": "TXN-65f1a2b3"
}
```
* **Response 200 (Gạch nợ thành công):**
```json
{
  "success": true,
  "data": {
    "student_id": "521H0001",
    "status": "PAID"
  }
}
```
* **Response 409 (Học phí đã được thanh toán trước đó):**
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

### 4.3 Hoàn tác gạch nợ (`POST /api/tuitions/revert`)
* **Mô tả:** Chuyển trạng thái từ `PAID` về `UNPAID` nếu xảy ra sự cố cần rollback.
* **Request Body:**
```json
{
  "student_id": "521H0001",
  "transaction_id": "TXN-65f1a2b3"
}
```
* **Response 200 (Hoàn tác thành công):**
```json
{
  "success": true,
  "data": {
    "student_id": "521H0001",
    "status": "UNPAID"
  }
}
```

---

## 5. Quy Tắc Concurrency & Atomic Settlement Bắt Buộc

> **Lưu ý quan trọng:**  
> **Tuyệt đối KHÔNG kiểm tra trạng thái bằng Python code rồi mới UPDATE.**  
> Phải gộp điều kiện kiểm tra `status = 'UNPAID'` vào trực tiếp câu lệnh SQL UPDATE để MySQL lock dòng (Row-level Lock).

### Câu lệnh SQL Atomic trong `tuition_repository.py`:
```sql
UPDATE tuitions 
SET status = 'PAID', 
    paid_at = NOW(), 
    paid_by = %s, 
    transaction_id = %s 
WHERE student_id = %s AND status = 'UNPAID';
```
* **Xử lý kết quả:**
  * `cursor.rowcount == 1`: Chỉ DUY NHẤT request đầu tiên cập nhật thành công $\rightarrow$ Trả kết quả thành công.
  * `cursor.rowcount == 0`: Hóa đơn này đã được thanh toán bởi một request khác trước đó $\rightarrow$ Ném lỗi `TUITION_ALREADY_PAID` (HTTP 409).

---

## 6. Biến Môi Trường (`.env`)

Tạo file `.env` từ `.env.example`:
```ini
DB_HOST=localhost
DB_PORT=8552
DB_USER=root
DB_PASSWORD=rootpassword
DB_NAME=tuition_db
```

---

## 7. Hướng Dẫn Chạy & Kiểm Thử Độc Lập

### 7.1 Cài đặt & Khởi chạy Service (Port 8732)
```bash
# 1. Di chuyển vào thư mục service
cd backend/tuition-service

# 2. Tạo virtual environment & cài dependencies
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac
pip install -r requirements.txt

# 3. Khởi chạy service
uvicorn app.main:app --host 0.0.0.0 --port 8732 --reload
```

### 7.2 Kiểm thử bằng cURL

#### 1. Tra cứu học phí sinh viên:
```bash
curl -X GET http://localhost:8732/api/tuitions/students/521H0001
```

#### 2. Thực hiện gạch nợ học phí:
```bash
curl -X POST http://localhost:8732/api/tuitions/pay \
  -H "Content-Type: application/json" \
  -d "{\"student_id\": \"521H0001\", \"paid_by\": \"1\", \"transaction_id\": \"TXN-TEST-001\"}"
```

#### 3. Thử gạch nợ lại lần 2 (Kiểm tra chặn concurrent/duplicate):
```bash
curl -X POST http://localhost:8732/api/tuitions/pay \
  -H "Content-Type: application/json" \
  -d "{\"student_id\": \"521H0001\", \"paid_by\": \"1\", \"transaction_id\": \"TXN-TEST-002\"}"
```
*(Kết quả mong đợi: Trả về lỗi 409 `TUITION_ALREADY_PAID`)*

#### 4. Hoàn tác gạch nợ:
```bash
curl -X POST http://localhost:8732/api/tuitions/revert \
  -H "Content-Type: application/json" \
  -d "{\"student_id\": \"521H0001\", \"transaction_id\": \"TXN-TEST-001\"}"
```

---

## 8. Bảng Kiểm Tra Nghiệm Thu (Checklist Cho Member 2)

- [ ] Kết nối `tuition_db` thành công qua connection pool `aiomysql`.
- [ ] `GET /students/521H0001` trả về đúng thông tin hóa đơn (student_name, major, amount, status).
- [ ] `GET /students/MSSV_KHONG_TON_TAI` trả về 404 `STUDENT_NOT_FOUND`.
- [ ] `POST /pay` lần đầu thành công, chuyển trạng thái sang `PAID`, lưu `paid_at`, `paid_by`, `transaction_id`.
- [ ] `POST /pay` lần 2 trên cùng một MSSV bị từ chối với mã lỗi 409 `TUITION_ALREADY_PAID`.
- [ ] `POST /revert` với đúng `transaction_id` chuyển trạng thái về `UNPAID`.
