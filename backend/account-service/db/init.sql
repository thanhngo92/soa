-- =============================================================================
-- Account Service Database Initialization (Member 1)
-- Database: account_db
-- =============================================================================

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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_balance CHECK (balance >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS account_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    balance_before DECIMAL(15, 2) NOT NULL,
    balance_after DECIMAL(15, 2) NOT NULL,
    reference_id VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_account_tx (account_id, created_at DESC),
    INDEX idx_ref_id (reference_id),
    UNIQUE KEY uq_account_ref_type (account_id, reference_id, transaction_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO accounts (id, username, password_hash, full_name, email, phone, balance) VALUES
(1, 'user01', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Nguyen Van An', 'nguyen.van.an@student.tdtu.edu.vn', '0901234567', 7500000.00),
(2, 'user02', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Tran Thi Bao', 'tran.thi.bao@student.tdtu.edu.vn', '0912345678', 2300000.00),
(3, 'user03', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Le Hoang Cuong', 'le.hoang.cuong@student.tdtu.edu.vn', '0923456789', 12000000.00),
(4, 'sv.nguyen', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Nguyen Van An', 'nguyen.van.an@student.tdtu.edu.vn', '0901234567', 7500000.00),
(5, 'sv.tran', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Tran Thi Bao', 'tran.thi.bao@student.tdtu.edu.vn', '0912345678', 2300000.00),
(6, 'sv.le', '$2b$12$ifwvjq2lDimPUy34suN.gegFUNu7tJossyjvWMUwLUwCdV3QHLRPS', 'Le Hoang Cuong', 'le.hoang.cuong@student.tdtu.edu.vn', '0923456789', 12000000.00)
ON DUPLICATE KEY UPDATE 
    username = VALUES(username),
    password_hash = VALUES(password_hash),
    full_name = VALUES(full_name),
    email = VALUES(email),
    phone = VALUES(phone),
    balance = VALUES(balance);
