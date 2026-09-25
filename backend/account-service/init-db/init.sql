-- =============================================================================
-- Account Service — MySQL Database Initialization
-- =============================================================================

CREATE DATABASE IF NOT EXISTS account_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE account_db;

-- ── accounts table ───────────────────────────────────────────────────────────
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

-- ── Seed Accounts ───────────────────────────────────────────────────────────
-- Test credentials (verified bcrypt hashes):
--   sv.nguyen / Test@123  → balance:  7,500,000 VND
--   sv.tran   / Test@123  → balance:  2,300,000 VND
--   sv.le     / Ibank@456 → balance: 12,000,000 VND

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
