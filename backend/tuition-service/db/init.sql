-- Tuition Service Database Schema (tuition_db)
SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS tuition_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tuition_db;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL UNIQUE,
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

INSERT INTO students (student_id, student_name, major) VALUES
('521H0001', 'Nguyễn Văn An',       'Công nghệ Thông tin'),
('521H0002', 'Trần Thị Bảo',        'Kế toán'),
('521H0003', 'Lê Hoàng Cường',      'Kỹ thuật Điện tử'),
('521H0010', 'Phạm Minh Đức',       'Kỹ thuật Phần mềm'),
('521H0025', 'Vũ Tuấn Kiệt',        'Khoa học Máy tính'),
('521H0034', 'Đặng Thùy Dung',      'Tài chính - Ngân hàng'),
('521H0056', 'Bùi Quốc Anh',        'Quản trị Kinh doanh'),
('521H0078', 'Đỗ Mai Phương',       'Ngôn ngữ Anh'),
('521H0089', 'Hồ Tấn Phát',         'Hệ thống Thông tin'),
('521H0099', 'Ngô Khánh Linh',      'Thương mại Điện tử'),
('522H0017', 'Phạm Đức Dũng',       'Quản trị Kinh doanh'),
('522H0041', 'Hoàng Thị Yến',       'Ngôn ngữ Anh'),
('522H0055', 'Trịnh Quốc Bảo',      'Kỹ thuật Phần mềm'),
('522H0063', 'Lý Gia Hưng',         'Công nghệ Thông tin'),
('522H0072', 'Dương Thúy Hằng',     'Kế toán'),
('522H0081', 'Trương Minh Khang',   'Khoa học Dữ liệu'),
('522H0094', 'Phan Thanh Thảo',     'Tài chính - Ngân hàng'),
('522H0105', 'Tô Hoài Nam',         'Kỹ thuật Điện tử'),
('523H0089', 'Võ Minh Khoa',        'Công nghệ Thông tin'),
('523H0102', 'Lê Quỳnh Nga',        'Kinh doanh Quốc tế'),
('523H0120', 'Nguyễn Đức Trọng',    'Kỹ thuật Phần mềm'),
('523H0145', 'Đinh Hồng Hạnh',      'Ngôn ngữ Trung'),
('523H0168', 'Cao Bá Quát',         'Khoa học Máy tính'),
('523H0189', 'Mai Văn Tiến',        'Hệ thống Thông tin'),
('523H0205', 'Trần Bảo Ngọc',       'Marketing'),
('523H0222', 'Hoàng Nhật Minh',     'Công nghệ Thông tin'),
('524H0012', 'Lê Phúc Thịnh',       'Trí tuệ Nhân tạo'),
('524H0031', 'Nguyễn Tấn Đạt',      'Công nghệ Thông tin'),
('524H0092', 'Lê Thanh Ngô',        'Kỹ thuật Phần mềm'),
('524H0136', 'Trần Nhật Huy',       'An toàn Thông tin')
ON DUPLICATE KEY UPDATE
    student_name = VALUES(student_name),
    major = VALUES(major);

INSERT INTO tuitions (student_id, semester, amount, status) VALUES
('521H0001', 'HK1/2024-2025', 4850000.00, 'UNPAID'),
('521H0002', 'HK1/2024-2025', 3620000.00, 'UNPAID'),
('521H0003', 'HK1/2024-2025', 3190000.00, 'UNPAID'),
('521H0003', 'HK2/2024-2025', 2000000.00, 'UNPAID'),
('521H0010', 'HK1/2024-2025', 5500000.00, 'UNPAID'),
('521H0025', 'HK1/2024-2025', 4100000.00, 'UNPAID'),
('521H0034', 'HK1/2024-2025', 4650000.00, 'UNPAID'),
('521H0056', 'HK1/2024-2025', 3800000.00, 'UNPAID'),
('521H0078', 'HK1/2024-2025', 4200000.00, 'UNPAID'),
('521H0089', 'HK1/2024-2025', 5300000.00, 'UNPAID'),
('521H0099', 'HK1/2024-2025', 4950000.00, 'UNPAID'),
('522H0017', 'HK1/2024-2025', 3450000.00, 'UNPAID'),
('522H0017', 'HK2/2024-2025', 3000000.00, 'UNPAID'),
('522H0041', 'HK1/2024-2025', 3280000.00, 'UNPAID'),
('522H0055', 'HK1/2024-2025', 7200000.00, 'UNPAID'),
('522H0063', 'HK1/2024-2025', 4900000.00, 'UNPAID'),
('522H0072', 'HK1/2024-2025', 3750000.00, 'UNPAID'),
('522H0081', 'HK1/2024-2025', 5600000.00, 'UNPAID'),
('522H0094', 'HK1/2024-2025', 4300000.00, 'UNPAID'),
('522H0105', 'HK1/2024-2025', 5100000.00, 'UNPAID'),
('523H0089', 'HK1/2024-2025', 4720000.00, 'UNPAID'),
('523H0102', 'HK1/2024-2025', 3900000.00, 'UNPAID'),
('523H0120', 'HK1/2024-2025', 5450000.00, 'UNPAID'),
('523H0145', 'HK1/2024-2025', 4150000.00, 'UNPAID'),
('523H0168', 'HK1/2024-2025', 5800000.00, 'UNPAID'),
('523H0189', 'HK1/2024-2025', 4600000.00, 'UNPAID'),
('523H0205', 'HK1/2024-2025', 4500000.00, 'UNPAID'),
('523H0222', 'HK1/2024-2025', 5250000.00, 'UNPAID'),
('524H0012', 'HK1/2024-2025', 6100000.00, 'UNPAID'),
('524H0031', 'HK1/2024-2025', 5900000.00, 'UNPAID'),
('524H0092', 'HK1/2024-2025', 5900000.00, 'UNPAID'),
('524H0136', 'HK1/2024-2025', 5900000.00, 'UNPAID')
ON DUPLICATE KEY UPDATE
    amount = VALUES(amount),
    status = VALUES(status),
    paid_at = IF(VALUES(status) = 'UNPAID', NULL, paid_at);
