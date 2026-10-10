-- =============================================================================
-- Tuition Service Database Initialization (Member 2)
-- Database: tuition_db
-- =============================================================================

CREATE DATABASE IF NOT EXISTS tuition_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tuition_db;

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

INSERT INTO tuitions (student_id, student_name, major, semester, amount, status) VALUES
('521H0001', 'Nguyen Van An',   'Cong nghe Thong tin', 'HK1/2024-2025', 4850000.00, 'UNPAID'),
('521H0002', 'Tran Thi Bao',    'Ke toan',             'HK1/2024-2025', 3620000.00, 'UNPAID'),
('521H0003', 'Le Hoang Cuong',  'Ky thuat Dien tu',    'HK1/2024-2025', 5130000.00, 'UNPAID'),
('522H0017', 'Pham Duc Dung',   'Quan tri Kinh doanh', 'HK1/2024-2025', 3975000.00, 'UNPAID'),
('522H0041', 'Hoang Thi Yen',   'Ngon ngu Anh',        'HK1/2024-2025', 3280000.00, 'UNPAID'),
('523H0089', 'Vo Minh Khoa',    'Cong nghe Thong tin', 'HK1/2024-2025', 4720000.00, 'UNPAID')
ON DUPLICATE KEY UPDATE
    student_name = VALUES(student_name),
    major = VALUES(major),
    semester = VALUES(semester),
    amount = VALUES(amount);
