# Tuition Service

Dịch vụ quản lý công nợ học phí sinh viên và gạch nợ nguyên tử trong hệ thống iBanking Tuition Payment System.

* **Công nghệ:** Python 3.11, FastAPI, aiomysql (MySQL 8.0)
* **Port:** `8732` (Qua Gateway: `/api/tuitions/...`)
* **Database:** `tuition_db` (MySQL Port `8552`)

---

## 1. Phạm Vi Chức Năng

1. **Quản lý Cơ sở dữ liệu `tuition_db` (Chuẩn 3NF):** Tách thành 2 bảng liên kết khóa ngoại (`FOREIGN KEY`):
   * Bảng `students`: Lưu trữ thông tin gốc của sinh viên (`student_id` PK, `student_name`, `major`).
   * Bảng `tuitions`: Lưu trữ công nợ học phí theo học kỳ (`id` PK, `student_id` FK tham chiếu `students(student_id)`, `semester`, `amount` CHECK `> 0`, `status` `UNPAID`/`PAID`, `paid_at`).
2. **Tra cứu học phí (`GET /students/{mssv}` & `GET /records/{tuition_id}`):** Yêu cầu xác thực người dùng (JWT) hoặc dịch vụ nội bộ (`X-Internal-Token`), kiểm tra định dạng MSSV (`6..10` ký tự chữ và số) và thực hiện `INNER JOIN` giữa `students` và `tuitions` để trả về thông tin sinh viên kèm khoản học phí.
3. **Gạch nợ nguyên tử (`POST /pay` — Internal Only):** Khóa bi quan `SELECT ... FOR UPDATE`, đối chiếu khớp chính xác `tuition_id`, `amount` và trạng thái `status = 'UNPAID'` trước khi cập nhật sang `PAID`, chống thanh toán trùng lặp hoặc lệch số tiền khi có nhiều giao dịch đồng thời.

---

## 2. Database Schema & Dữ Liệu Mẫu (`tuition_db`)

```sql
CREATE TABLE IF NOT EXISTS students (
    student_id VARCHAR(20) PRIMARY KEY,
    student_name VARCHAR(255) NOT NULL,
    major VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tuitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL,
    semester VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UNPAID',
    paid_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tuition_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_tuition_amount CHECK (amount > 0),
    CONSTRAINT chk_tuition_status CHECK (status IN ('UNPAID', 'PAID')),
    CONSTRAINT chk_tuition_paid_integrity CHECK (
        (status = 'UNPAID' AND paid_at IS NULL)
        OR (status = 'PAID' AND paid_at IS NOT NULL)
    ),
    UNIQUE KEY uq_student_semester (student_id, semester)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Dữ liệu mẫu
| MSSV (`student_id`) | Họ và Tên | Ngành | Học kỳ | Học phí (VND) | Trạng thái |
|:---|:---|:---|:---|:---|:---|
| `521H0001` | Nguyễn Văn An | Công nghệ Thông tin | HK1/2024-2025 | 4,850,000 | `UNPAID` |
| `521H0002` | Trần Thị Bảo | Kế toán | HK1/2024-2025 | 3,620,000 | `UNPAID` |
| `521H0003` | Lê Hoàng Cường | Kỹ thuật Điện tử | HK1/2024-2025 | 5,190,000 | `UNPAID` |
| `522H0017` | Phạm Đức Dũng | Quản trị Kinh doanh | HK1/2024-2025 | 6,450,000 | `UNPAID` |
| `522H0041` | Hoàng Thị Yến | Ngôn ngữ Anh | HK1/2024-2025 | 3,280,000 | `UNPAID` |
| `523H0089` | Võ Minh Khoa | Công nghệ Thông tin | HK1/2024-2025 | 4,720,000 | `UNPAID` |

---

## 3. Đặc Tả API Endpoints

* **`GET /api/tuitions/students/{mssv}`**
  * Header: `Authorization: Bearer <access_token>` (hoặc `X-Internal-Token`)
  * Response `200`: `{"success": true, "data": {"tuition_id": 1, "student_id": "521H0001", "student_name": "Nguyen Van An", "major": "Cong nghe Thong tin", "semester": "HK1/2024-2025", "amount": 4850000.0, "status": "UNPAID", "paid_at": null}}`
  * Response `400`: `INVALID_MSSV_FORMAT` | `401`: `UNAUTHORIZED` | `404`: `STUDENT_NOT_FOUND`
* **`GET /api/tuitions/records/{tuition_id}`**
  * Header: `Authorization: Bearer <access_token>` (hoặc `X-Internal-Token`)
  * Response `200`: `{"success": true, "data": {"tuition_id": 1, "student_id": "521H0001", "student_name": "Nguyen Van An", "major": "Cong nghe Thong tin", "semester": "HK1/2024-2025", "amount": 4850000.0, "status": "PAID", "paid_at": "..."}}`
* **`POST /api/tuitions/pay`** *(Internal Only)*
  * Header: `X-Internal-Token: <INTERNAL_SERVICE_KEY>`
  * Request: `{"tuition_id": 1, "amount": 4850000.0}`
  * Response `200`: `{"success": true, "data": {"tuition_id": 1, "student_id": "521H0001", "student_name": "Nguyen Van An", "semester": "HK1/2024-2025", "status": "PAID", "paid_at": "..."}}`
  * Response `409`: `TUITION_ALREADY_PAID`
