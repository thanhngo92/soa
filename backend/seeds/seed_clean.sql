-- Seed chuẩn theo đúng yêu cầu đề bài: Mỗi sinh viên duy nhất 1 khoản nợ
SET NAMES utf8mb4;

-- 1. Tài khoản nhiều tiền (mật khẩu: Test@123)
USE account_db;
TRUNCATE TABLE account_transactions;
INSERT INTO accounts (id, username, password_hash, full_name, email, phone, balance) VALUES
(1, 'sv.nguyen', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Nguyễn Văn An', 'nguyen.van.an@student.tdtu.edu.vn', '0901234567', 50000000.00),
(2, 'sv.tran', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Trần Thị Bảo', 'tran.thi.bao@student.tdtu.edu.vn', '0912345678', 35000000.00),
(3, 'sv.le', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Lê Hoàng Cường', 'le.hoang.cuong@student.tdtu.edu.vn', '0923456789', 80000000.00),
(4, 'sv.pham', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Phạm Minh Đức', 'pham.minh.duc@student.tdtu.edu.vn', '0934567890', 25000000.00),
(5, 'sv.hoang', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Hoàng Thùy Linh', 'hoang.thuy.linh@student.tdtu.edu.vn', '0945678901', 40000000.00),
(6, 'sv.vu', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Vũ Tuấn Kiệt', 'vu.tuan.kiet@student.tdtu.edu.vn', '0956789012', 60000000.00),
(7, 'sv.ngheo', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Đỗ Văn Ít Tiền (Test thiếu tiền)', 'do.van.it.tien@student.tdtu.edu.vn', '0967890123', 500000.00)
ON DUPLICATE KEY UPDATE
    full_name = VALUES(full_name),
    email = VALUES(email),
    phone = VALUES(phone),
    balance = VALUES(balance);

-- 2. Dữ liệu học phí chuẩn: 1 sinh viên = 1 khoản nợ duy nhất
USE tuition_db;
DELETE FROM tuitions;
DELETE FROM students;

INSERT INTO students (student_id, student_name, major) VALUES
('521H0001', 'Nguyễn Văn An',  'Công nghệ Thông tin'),
('521H0002', 'Trần Thị Bảo',   'Kế toán'),
('521H0003', 'Lê Hoàng Cường', 'Kỹ thuật Điện tử'),
('522H0017', 'Phạm Đức Dũng',  'Quản trị Kinh doanh'),
('522H0041', 'Hoàng Thị Yến',  'Ngôn ngữ Anh'),
('523H0089', 'Võ Minh Khoa',   'Công nghệ Thông tin'),
('521H0010', 'Bùi Quốc Hùng',  'Kỹ thuật Phần mềm'),
('521H0025', 'Đặng Thảo My',   'Tài chính Ngân hàng'),
('522H0055', 'Ngô Kiến Huy',   'Khoa học Máy tính'),
('523H0102', 'Dương Gia Bảo',  'Luật Kinh tế'),
('523H0205', 'Hồ Ngọc Hà',     'Mỹ thuật Công nghiệp'),
('524H0012', 'Phan Thanh Bình', 'Kỹ thuật Ô tô');

INSERT INTO tuitions (student_id, semester, amount, status, paid_at) VALUES
('521H0001', 'HK1/2024-2025', 4850000.00, 'UNPAID', NULL),
('521H0002', 'HK1/2024-2025', 3620000.00, 'UNPAID', NULL),
('521H0003', 'HK1/2024-2025', 5190000.00, 'UNPAID', NULL),
('522H0017', 'HK1/2024-2025', 6450000.00, 'UNPAID', NULL),
('522H0041', 'HK1/2024-2025', 3280000.00, 'UNPAID', NULL),
('523H0089', 'HK1/2024-2025', 4720000.00, 'UNPAID', NULL),
('521H0010', 'HK1/2024-2025', 5500000.00, 'UNPAID', NULL),
('521H0025', 'HK1/2024-2025', 4100000.00, 'UNPAID', NULL),
('522H0055', 'HK1/2024-2025', 7200000.00, 'UNPAID', NULL),
('523H0102', 'HK1/2024-2025', 3900000.00, 'UNPAID', NULL),
('523H0205', 'HK1/2024-2025', 6800000.00, 'UNPAID', NULL),
('524H0012', 'HK1/2024-2025', 5300000.00, 'UNPAID', NULL);

-- 3. Reset bảng thanh toán & OTP để test sạch
USE payment_db;
TRUNCATE TABLE payments;

USE notification_db;
TRUNCATE TABLE otps;
