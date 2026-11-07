# Backend Microservices — Kiến Trúc & Hướng Dẫn Phát Triển

Hệ thống các dịch vụ phụ trợ của iBanking Tuition Payment System, phát triển bằng Python 3.11, FastAPI, MySQL 8.0 (`aiomysql`), HTTPX và Mailpit.

---

## 1. Danh Mục Microservices & Cổng Mạng

```text
Frontend :3000
   |
   v
API Gateway :8877
   |-- Account Service :8661 ------- account_db (MySQL :8552)
   |-- Tuition Service :8732 ------- tuition_db (MySQL :8552)
   |-- Payment Service :8815 ------- payment_db (MySQL :8552)
   +-- Notification Service :8940 -- notification_db (MySQL :8552)
                                     Mailpit SMTP :1025 / Web :8025
```

| Dịch Vụ | Port | Công nghệ | Cơ sở dữ liệu | Chức năng chính |
|:---|:---|:---|:---|:---|
| `account-service` | `8661` | FastAPI, Bcrypt, PyJWT | `account_db` | Xác thực JWT, thông tin tài khoản, trừ/hoàn tiền ACID |
| `tuition-service` | `8732` | FastAPI, aiomysql | `tuition_db` | Tra cứu học phí theo MSSV, gạch nợ hóa đơn nguyên tử |
| `notification-service` | `8940` | FastAPI, smtplib | `notification_db` | Sinh OTP 6 số (5 phút), xác thực dùng một lần, gửi email |
| `payment-service` | `8815` | FastAPI, HTTPX | `payment_db` | Saga Orchestrator, điều phối thanh toán & hoàn tiền bù trừ |

---

## 2. Cấu Trúc Thư Mục Từng Microservice

```text
backend/{service-name}/
|-- Dockerfile                   # Cấu hình đóng gói container
|-- requirements.txt             # Danh sách thư viện Python
|-- .env.example                 # Mẫu biến môi trường
|-- README.md                    # Tài liệu chi tiết của service
|-- db/
|   +-- init.sql                 # Script khởi tạo schema, constraints, dữ liệu mẫu
|
+-- app/
    |-- main.py                  # Điểm vào ứng dụng, quản lý vòng đời DB pool / HTTP client
    |-- config/
    |   |-- env.py               # Cấu hình biến môi trường qua Pydantic Settings
    |   +-- database.py          # Quản lý kết nối bất đồng bộ aiomysql
    |-- routes/                  # Định nghĩa các URI endpoint & HTTP method
    |-- middlewares/             # Kiểm tra xác thực JWT / Internal Token & xử lý lỗi toàn cục
    |-- controllers/             # Tiếp nhận request DTO, gọi tầng service, đóng gói response
    |-- services/                # Xử lý nghiệp vụ và điều phối quy trình
    |-- repositories/            # Truy vấn và cập nhật dữ liệu trên MySQL
    |-- schemas/                 # Mô hình dữ liệu đầu vào/đầu ra Pydantic
    |-- utils/                   # Định dạng phản hồi JSON và lớp ngoại lệ AppError
    +-- clients/                 # HTTP client giao tiếp nội bộ giữa các service
```

---

## 3. Luồng Xử Lý Phân Lớp

```text
Route -> Middleware -> Controller -> Service -> Repository -> Database
```

* `Route`: Khai báo đường dẫn URI và phương thức HTTP.
* `Middleware`: Xác thực JWT hoặc `X-Internal-Token` và chuẩn hóa lỗi trả về.
* `Controller`: Nhận dữ liệu đã kiểm tra qua Pydantic DTO, gọi `Service` và trả kết quả qua `response_util.py`.
* `Service`: Thực hiện logic nghiệp vụ và điều phối Saga.
* `Repository`: Thực thi các câu lệnh SQL và giao dịch ACID trên MySQL.

---

## 4. Nguyên Tắc Thiết Kế

### 4.1 Cô lập Cơ sở dữ liệu (Database-per-Service)
* Mỗi service chỉ kết nối và thao tác trên cơ sở dữ liệu riêng của mình.
* Không thiết lập khóa ngoại vật lý xuyên cơ sở dữ liệu; mọi tương tác liên dịch vụ đều thực hiện qua REST API nội bộ.

### 4.2 Kiểm soát đồng thời & Giao dịch ACID
* **Trừ số dư tài khoản (`account-service`):** Khóa dòng `SELECT ... FOR UPDATE`, cập nhật điều kiện `balance >= amount` và ghi nhận vào bảng `account_transactions` trong cùng một ACID transaction.
* **Gạch nợ học phí (`tuition-service`):** Cập nhật nguyên tử `UPDATE tuitions SET status = 'PAID', ... WHERE student_id = %s AND semester = %s AND status = 'UNPAID'` và kiểm tra `cur.rowcount`.
* **Xác thực OTP (`notification-service`):** Khóa dòng `SELECT ... FOR UPDATE`, kiểm tra thời hạn 5 phút, giới hạn tối đa 3 lần nhập và đánh dấu `is_used = TRUE` nguyên tử.

### 4.3 Bù trừ giao dịch Saga (`payment-service`)
* Khi bước trừ tiền tại `account-service` thành công nhưng bước gạch nợ tại `tuition-service` bị từ chối, `payment-service` tự động gọi `POST /api/accounts/refund` để hoàn trả số dư và chuyển trạng thái thanh toán sang `FAILED`.

---

## 5. Khởi Chạy Hệ Thống

Từ thư mục gốc của dự án:

```bash
docker compose up --build -d
```
