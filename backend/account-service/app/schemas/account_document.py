# MySQL Table Schema — accounts table
#
# CREATE TABLE accounts (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     username VARCHAR(100) NOT NULL UNIQUE,
#     password_hash VARCHAR(255) NOT NULL,
#     full_name VARCHAR(255) NOT NULL,
#     email VARCHAR(255) NOT NULL,
#     phone VARCHAR(50) NOT NULL,
#     balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     CONSTRAINT chk_balance CHECK (balance >= 0)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
