-- Nạp dữ liệu mở rộng 30 sinh viên từ 521H0001 đến 521H0030 phục vụ demo
SET NAMES utf8mb4;

-- 1. Làm sạch và nạp lại tài khoản iBanking (mật khẩu chung: Test@123)
USE account_db;
TRUNCATE TABLE account_transactions;

INSERT INTO accounts (id, username, password_hash, full_name, email, phone, balance) VALUES
(1, 'sv.nguyen', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Nguyễn Văn An', 'nguyen.van.an@student.tdtu.edu.vn', '0901234567', 100000000.00),
(2, 'sv.tran', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Trần Thị Bảo', 'tran.thi.bao@student.tdtu.edu.vn', '0912345678', 100000000.00),
(3, 'sv.le', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Lê Hoàng Cường', 'le.hoang.cuong@student.tdtu.edu.vn', '0923456789', 100000000.00),
(4, 'sv.pham', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Phạm Minh Đức', 'pham.minh.duc@student.tdtu.edu.vn', '0934567890', 50000000.00),
(5, 'sv.hoang', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Hoàng Thùy Linh', 'hoang.thuy.linh@student.tdtu.edu.vn', '0945678901', 50000000.00),
(6, 'sv.vu', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Vũ Tuấn Kiệt', 'vu.tuan.kiet@student.tdtu.edu.vn', '0956789012', 50000000.00),
(7, 'sv.ngheo', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Đỗ Văn Ít Tiền (Test thiếu tiền)', 'do.van.it.tien@student.tdtu.edu.vn', '0967890123', 500000.00)
ON DUPLICATE KEY UPDATE
    full_name = VALUES(full_name),
    email = VALUES(email),
    phone = VALUES(phone),
    balance = VALUES(balance);

-- 2. Làm sạch và nạp 30 sinh viên từ 521H0001 đến 521H0030
USE tuition_db;
DELETE FROM tuitions;
DELETE FROM students;

INSERT INTO students (student_id, student_name, major) VALUES
('521H0001', 'Nguyễn Văn An', 'Công nghệ Thông tin'),
('521H0002', 'Trần Thị Bảo', 'Kế toán'),
('521H0003', 'Lê Hoàng Cường', 'Kỹ thuật Điện tử'),
('521H0004', 'Phạm Đức Dũng', 'Quản trị Kinh doanh'),
('521H0005', 'Hoàng Thị Yến', 'Ngôn ngữ Anh'),
('521H0006', 'Võ Minh Khoa', 'Công nghệ Thông tin'),
('521H0007', 'Đặng Quốc Huy', 'Kỹ thuật Phần mềm'),
('521H0008', 'Bùi Thảo My', 'Tài chính Ngân hàng'),
('521H0009', 'Đỗ Thành Nam', 'Khoa học Máy tính'),
('521H0010', 'Ngô Gia Bảo', 'Luật Kinh tế'),
('521H0011', 'Dương Ngọc Hà', 'Mỹ thuật Công nghiệp'),
('521H0012', 'Phan Thanh Bình', 'Kỹ thuật Ô tô'),
('521H0013', 'Hồ Quang Hiếu', 'Marketing'),
('521H0014', 'Lý Hải Đăng', 'Logistics'),
('521H0015', 'Mai Phương Thúy', 'Quan hệ Quốc tế'),
('521H0016', 'Trịnh Thăng Bình', 'Công nghệ Sinh học'),
('521H0017', 'Đinh Tiến Đạt', 'Kiến trúc'),
('521H0018', 'Cao Thái Sơn', 'Kỹ thuật Xây dựng'),
('521H0019', 'Lương Bích Hữu', 'Dược học'),
('521H0020', 'Ưng Hoàng Phúc', 'Kinh doanh Quốc tế'),
('521H0021', 'Châu Đăng Khoa', 'Công nghệ Thông tin'),
('521H0022', 'Trần Bảo Thy', 'Thiết kế Đồ họa'),
('521H0023', 'Nguyễn Đông Nhi', 'Quản trị Khách sạn'),
('521H0024', 'Lê Ông Cao Thắng', 'Kỹ thuật Điều khiển'),
('521H0025', 'Vũ Cát Tường', 'Khoa học Dữ liệu'),
('521H0026', 'Tóc Tiên', 'Hóa học Ứng dụng'),
('521H0027', 'Bùi Anh Tuấn', 'Toán Tin Ứng dụng'),
('521H0028', 'Hà Anh Tuấn', 'Tài chính Doanh nghiệp'),
('521H0029', 'Đen Vâu', 'Truyền thông Đa phương tiện'),
('521H0030', 'Sơn Tùng M-TP', 'Công nghệ Âm nhạc');

INSERT INTO tuitions (student_id, semester, amount, status, paid_at) VALUES
('521H0001', 'HK1/2024-2025', 4850000.00, 'UNPAID', NULL),
('521H0002', 'HK1/2024-2025', 3620000.00, 'UNPAID', NULL),
('521H0003', 'HK1/2024-2025', 5190000.00, 'UNPAID', NULL),
('521H0004', 'HK1/2024-2025', 6450000.00, 'UNPAID', NULL),
('521H0005', 'HK1/2024-2025', 4500000.00, 'UNPAID', NULL),
('521H0006', 'HK1/2024-2025', 4720000.00, 'UNPAID', NULL),
('521H0007', 'HK1/2024-2025', 5500000.00, 'UNPAID', NULL),
('521H0008', 'HK1/2024-2025', 4100000.00, 'UNPAID', NULL),
('521H0009', 'HK1/2024-2025', 7200000.00, 'UNPAID', NULL),
('521H0010', 'HK1/2024-2025', 3900000.00, 'UNPAID', NULL),
('521H0011', 'HK1/2024-2025', 6800000.00, 'UNPAID', NULL),
('521H0012', 'HK1/2024-2025', 5300000.00, 'UNPAID', NULL),
('521H0013', 'HK1/2024-2025', 4600000.00, 'UNPAID', NULL),
('521H0014', 'HK1/2024-2025', 5800000.00, 'UNPAID', NULL),
('521H0015', 'HK1/2024-2025', 4200000.00, 'UNPAID', NULL),
('521H0016', 'HK1/2024-2025', 6100000.00, 'UNPAID', NULL),
('521H0017', 'HK1/2024-2025', 5900000.00, 'UNPAID', NULL),
('521H0018', 'HK1/2024-2025', 6300000.00, 'UNPAID', NULL),
('521H0019', 'HK1/2024-2025', 7500000.00, 'UNPAID', NULL),
('521H0020', 'HK1/2024-2025', 4900000.00, 'UNPAID', NULL),
('521H0021', 'HK1/2024-2025', 5200000.00, 'UNPAID', NULL),
('521H0022', 'HK1/2024-2025', 4400000.00, 'UNPAID', NULL),
('521H0023', 'HK1/2024-2025', 5100000.00, 'UNPAID', NULL),
('521H0024', 'HK1/2024-2025', 5700000.00, 'UNPAID', NULL),
('521H0025', 'HK1/2024-2025', 6600000.00, 'UNPAID', NULL),
('521H0026', 'HK1/2024-2025', 4800000.00, 'UNPAID', NULL),
('521H0027', 'HK1/2024-2025', 5400000.00, 'UNPAID', NULL),
('521H0028', 'HK1/2024-2025', 5000000.00, 'UNPAID', NULL),
('521H0029', 'HK1/2024-2025', 4700000.00, 'UNPAID', NULL),
('521H0030', 'HK1/2024-2025', 8500000.00, 'UNPAID', NULL);

-- 3. Làm sạch lịch sử giao dịch & OTP
USE payment_db;
TRUNCATE TABLE payments;

USE notification_db;
TRUNCATE TABLE otps;
