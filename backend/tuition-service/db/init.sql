-- Tuition Service Database Schema (tuition_db)
SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS tuition_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tuition_db;

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

INSERT INTO students (student_id, student_name, major) VALUES
('521H0001', 'Nguyễn Văn An',  'Công nghệ Thông tin'),
('521H0002', 'Trần Thị Bảo',   'Kế toán'),
('521H0003', 'Lê Hoàng Cường', 'Kỹ thuật Điện tử'),
('522H0017', 'Phạm Đức Dũng',  'Quản trị Kinh doanh'),
('522H0041', 'Hoàng Thị Yến',  'Ngôn ngữ Anh'),
('523H0089', 'Võ Minh Khoa',   'Công nghệ Thông tin')
ON DUPLICATE KEY UPDATE
    student_name = VALUES(student_name),
    major = VALUES(major);

INSERT INTO tuitions (student_id, semester, amount, status) VALUES
('521H0001', 'HK1/2024-2025', 4850000.00, 'UNPAID'),
('521H0002', 'HK1/2024-2025', 3620000.00, 'UNPAID'),
('521H0003', 'HK1/2024-2025', 3190000.00, 'UNPAID'),
('521H0003', 'HK2/2024-2025', 2000000.00, 'UNPAID'),
('522H0017', 'HK1/2024-2025', 3450000.00, 'UNPAID'),
('522H0017', 'HK2/2024-2025', 3000000.00, 'UNPAID'),
('522H0041', 'HK1/2024-2025', 3280000.00, 'UNPAID'),
('523H0089', 'HK1/2024-2025', 4720000.00, 'UNPAID')
ON DUPLICATE KEY UPDATE
    amount = VALUES(amount),
    status = VALUES(status);
