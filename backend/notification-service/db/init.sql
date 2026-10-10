-- =============================================================================
-- Notification Service Database Initialization (Member 2)
-- Database: notification_db
-- =============================================================================

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
    attempts INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_payment_id (payment_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_verify_otp (payment_id, otp_code, is_used)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
