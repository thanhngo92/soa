# Database Seed Scripts

Thư mục chứa các tệp SQL nạp dữ liệu mẫu (Seed Data) phục vụ demo và kiểm thử:

* `seed_30_students.sql`: Nạp 30 sinh viên từ `521H0001` đến `521H0030` cùng các tài khoản thử nghiệm.
* `seed_clean.sql`: Nạp bộ dữ liệu cơ bản theo chuẩn đề bài (mỗi sinh viên nợ 1 học kỳ).
* `seed_expanded.sql`: Nạp dữ liệu mở rộng cho các tình huống kiểm thử số dư và nhiều khoản nợ.

### Cách nạp dữ liệu vào MySQL Docker:

```bash
# Nạp 30 sinh viên mẫu:
Get-Content backend/seeds/seed_30_students.sql -Encoding utf8 | docker compose exec -T mysql mysql --default-character-set=utf8mb4 -uroot -prootpassword

# Nạp dữ liệu cơ bản:
Get-Content backend/seeds/seed_clean.sql -Encoding utf8 | docker compose exec -T mysql mysql --default-character-set=utf8mb4 -uroot -prootpassword
```
