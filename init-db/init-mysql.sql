-- =============================================================================
-- MySQL Initialization Script for All Microservices
-- Port: 8552
-- =============================================================================

-- ── 1. ACCOUNT SERVICE DATABASE ──────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS account_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE account_db;

CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_balance CHECK (balance >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO accounts (id, username, password_hash, full_name, email, phone, balance) VALUES
(1, 'sv.nguyen', '$2b$12$kEJGg8fVLyvUhWg2zsBY1ejZ.KFf1oRRPgrbTgOJmwUye9/50vcUi', 'Nguyen Van An', 'nguyen.van.an@student.tdtu.edu.vn', '0901234567', 7500000.00),
(2, 'sv.tran',   '$2b$12$kEJGg8fVLyvUhWg2zsBY1ejZ.KFf1oRRPgrbTgOJmwUye9/50vcUi', 'Tran Thi Bao', 'tran.thi.bao@student.tdtu.edu.vn', '0912345678', 2300000.00),
(3, 'sv.le',     '$2b$12$9FoyHF0vwXN4C1PGu/YQCuNZowPWs5DzatcZuvm2VOZ7pMSjMG5BC', 'Le Hoang Cuong', 'le.hoang.cuong@student.tdtu.edu.vn', '0923456789', 12000000.00)
ON DUPLICATE KEY UPDATE 
    password_hash = VALUES(password_hash),
    full_name = VALUES(full_name),
    email = VALUES(email),
    phone = VALUES(phone),
    balance = VALUES(balance);


-- ── 2. TUITION SERVICE DATABASE ──────────────────────────────────────────────
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


-- ── 3. PAYMENT SERVICE DATABASE ──────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS payment_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE payment_db;

CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    student_id VARCHAR(50) NOT NULL,
    student_name VARCHAR(255) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    error_code VARCHAR(50) NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── 4. NOTIFICATION SERVICE DATABASE ────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS notification_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE notification_db;

CREATE TABLE IF NOT EXISTS otps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id VARCHAR(50) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_payment_id (payment_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
