# Tuition Service

Dịch vụ quản lý công nợ học phí sinh viên và gạch nợ nguyên tử trong hệ thống iBanking Tuition Payment System.

* **Công nghệ:** Python 3.11, FastAPI, aiomysql (MySQL 8.0)
* **Port:** `8732` (Qua Gateway: `/api/tuitions/...`)
* **Database:** `tuition_db` (MySQL Port `8552`)

---

## 1. Phạm Vi Chức Năng

1. **Quản lý Cơ sở dữ liệu `tuition_db`:** Lưu trữ thông tin sinh viên, ngành học, học kỳ, số tiền học phí và trạng thái thanh toán (`UNPAID` / `PAID`).
2. **Tra cứu học phí (`GET /students/{mssv}`):** Yêu cầu xác thực người dùng (JWT) hoặc dịch vụ nội bộ (`X-Internal-Token`), kiểm tra định dạng MSSV (`6..10` ký tự chữ và số) và trả về thông tin công nợ.
3. **Gạch nợ nguyên tử (`POST /pay` — Internal Only):** Cập nhật trạng thái từ `UNPAID` sang `PAID` bằng câu lệnh điều kiện nguyên tử ở tầng MySQL, chống thanh toán trùng lặp khi có nhiều giao dịch đồng thời.
4. **Hoàn tác trạng thái (`POST /revert` — Internal Only):** Hỗ trợ khôi phục trạng thái học phí về `UNPAID` phục vụ kiểm thử.

---

## 2. Database Schema & Dữ Liệu Mẫu (`tuition_db`)

```sql
CREATE TABLE IF NOT EXISTS tuitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    student_name VARCHAR(255) NOT NULL,
    major VARCHAR(255) NOT NULL,
    semester VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UNPAID',
    paid_at TIMESTAMP NULL DEFAULT NULL,
    paid_by VARCHAR(50) NULL DEFAULT NULL,
    transaction_id VARCHAR(100) NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tuition_status CHECK (status IN ('UNPAID', 'PAID')),
    UNIQUE KEY uq_student_semester (student_id, semester)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Dữ liệu mẫu
| MSSV (`student_id`) | Họ và Tên | Ngành | Học kỳ | Học phí (VND) | Trạng thái |
|:---|:---|:---|:---|:---|:---|
| `521H0001` | Nguyen Van An | Cong nghe Thong tin | HK1/2024-2025 | 4,850,000 | `UNPAID` |
| `521H0002` | Tran Thi Bao | Ke toan | HK1/2024-2025 | 3,620,000 | `UNPAID` |
| `521H0003` | Le Hoang Cuong | Ky thuat Dien tu | HK1/2024-2025 | 5,130,000 | `UNPAID` |
| `522H0017` | Pham Duc Dung | Quan tri Kinh doanh | HK1/2024-2025 | 3,975,000 | `UNPAID` |
| `522H0041` | Hoang Thi Yen | Ngon ngu Anh | HK1/2024-2025 | 3,280,000 | `UNPAID` |
| `523H0089` | Vo Minh Khoa | Cong nghe Thong tin | HK1/2024-2025 | 4,720,000 | `UNPAID` |

---

## 3. Đặc Tả API Endpoints

* **`GET /api/tuitions/students/{mssv}`**
  * Header: `Authorization: Bearer <access_token>` (hoặc `X-Internal-Token`)
  * Response `200`: `{"success": true, "data": {"student_id": "521H0001", "student_name": "Nguyen Van An", "major": "Cong nghe Thong tin", "semester": "HK1/2024-2025", "amount": 4850000.0, "status": "UNPAID", "paid_at": null}}`
  * Response `400`: `INVALID_MSSV_FORMAT` | `401`: `UNAUTHORIZED` | `404`: `STUDENT_NOT_FOUND`
* **`POST /api/tuitions/pay`** *(Internal Only)*
  * Header: `X-Internal-Token: <INTERNAL_SERVICE_KEY>`
  * Request: `{"student_id": "521H0001", "paid_by": "1", "transaction_id": "1", "semester": "HK1/2024-2025"}`
  * Response `200`: `{"success": true, "data": {"student_id": "521H0001", "status": "PAID", "paid_at": "..."}}`
  * Response `409`: `TUITION_ALREADY_PAID`
