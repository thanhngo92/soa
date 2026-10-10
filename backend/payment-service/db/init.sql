-- =============================================================================
-- Payment Service Database Initialization (Member 3)
-- Database: payment_db
-- =============================================================================

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
    semester VARCHAR(50) NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    INDEX idx_student_id (student_id),
    INDEX idx_account_created (account_id, created_at DESC),
    CONSTRAINT chk_payment_status CHECK (status IN ('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
