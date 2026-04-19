-- ============================================================
--  Online Payment Fraud Detection — MySQL Schema
--  Developed by: ANILREDDY  |  Mobile: 9686809509
--  Run once: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS opfd_india
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE opfd_india;

CREATE TABLE IF NOT EXISTS users (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(60)  NOT NULL UNIQUE,
    email          VARCHAR(120) NOT NULL UNIQUE,
    password_hash  VARCHAR(256) NOT NULL,
    full_name      VARCHAR(120),
    mobile         VARCHAR(12),
    role           ENUM('user','admin') DEFAULT 'user',
    is_active      TINYINT(1) DEFAULT 1,
    otp_enabled    TINYINT(1) DEFAULT 0,
    email_verified TINYINT(1) DEFAULT 0,
    verify_token   VARCHAR(64),
    reset_token    VARCHAR(64),
    reset_expires  DATETIME,
    avatar_color   VARCHAR(20) DEFAULT '#FF9933',
    state          VARCHAR(50),
    bio            VARCHAR(200),
    last_login     DATETIME,
    login_attempts TINYINT DEFAULT 0,
    locked_until   DATETIME,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transactions (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    step             INT,
    type             VARCHAR(20),
    amount_inr       DECIMAL(18,2),
    old_balance_orig DECIMAL(18,2),
    new_balance_orig DECIMAL(18,2),
    old_balance_dest DECIMAL(18,2),
    new_balance_dest DECIMAL(18,2),
    prediction       ENUM('Fraud','Legitimate') NOT NULL,
    confidence       DECIMAL(5,2),
    risk_score       TINYINT UNSIGNED,
    ip_address       VARCHAR(45),
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS alerts (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    transaction_id INT,
    alert_type     VARCHAR(40),
    message        TEXT,
    is_read        TINYINT(1) DEFAULT 0,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)        REFERENCES users(id)        ON DELETE CASCADE,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_log (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT,
    action     VARCHAR(60),
    details    TEXT,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS otp_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    otp_code   VARCHAR(6) NOT NULL,
    purpose    VARCHAR(30) DEFAULT 'login',
    is_used    TINYINT(1) DEFAULT 0,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS system_settings (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    setting_key   VARCHAR(60) UNIQUE NOT NULL,
    setting_value TEXT,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ip_blacklist (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    reason     VARCHAR(200),
    blocked_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Default admin (password: Admin@123)
-- NOTE: Real hash is generated on first app run
INSERT IGNORE INTO users (username, email, password_hash, full_name, role, email_verified)
VALUES ('admin','anilreddy@opfd.in',
        'pbkdf2:sha256:600000$placeholder$hash',
        'ANILREDDY','admin',1);
