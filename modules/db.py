"""
modules/db.py
MySQL connection + auto-create all tables
Developed by ANILREDDY | 9686809509
"""

import os

# 🔥 SAFE MODE FLAG (Render detection)
DB_ENABLED = True
if os.environ.get("RENDER") or os.environ.get("DISABLE_DB") == "1":
    print("⚠️ DB DISABLED (Render mode)")
    DB_ENABLED = False


# 🔥 ADD: Safe import fallback (Windows fix)
try:
    from flask_mysqldb import MySQL
except ModuleNotFoundError:
    import pymysql
    pymysql.install_as_MySQLdb()
    try:
        from flask_mysqldb import MySQL
    except:
        DB_ENABLED = False
        MySQL = None

# 🔥 Initialize MySQL only if enabled
mysql = MySQL() if DB_ENABLED and MySQL else None


def get_cursor():
    if not DB_ENABLED or not mysql:
        print("⚠️ get_cursor skipped (DB disabled)")
        return None

    from flask import g
    if "db_conn" not in g:
        g.db_conn = mysql.connection
    return g.db_conn.cursor()


def query(sql, args=()):
    if not DB_ENABLED:
        print("⚠️ query skipped:", sql)
        return []

    cur = get_cursor()
    if not cur:
        return []
    cur.execute(sql, args)
    return cur.fetchall()


def query_one(sql, args=()):
    if not DB_ENABLED:
        print("⚠️ query_one skipped:", sql)
        return None

    cur = get_cursor()
    if not cur:
        return None
    cur.execute(sql, args)
    return cur.fetchone()


def execute(sql, args=()):
    if not DB_ENABLED:
        print("⚠️ execute skipped:", sql)
        return 0

    conn = mysql.connection
    cur  = conn.cursor()
    cur.execute(sql, args)
    conn.commit()
    return cur.lastrowid


def init_db(app):
    if not DB_ENABLED:
        print("⚠️ init_db skipped (DB disabled)")
        return

    mysql.init_app(app)

    try:
        with app.app_context():
            conn = mysql.connection
            cur  = conn.cursor()

            # ── users ──────────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(60) NOT NULL,
                    email VARCHAR(120) NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    full_name VARCHAR(120),
                    mobile VARCHAR(12),
                    role ENUM('user','admin') DEFAULT 'user',
                    is_active TINYINT(1) DEFAULT 1,
                    otp_enabled TINYINT(1) DEFAULT 0,
                    email_verified TINYINT(1) DEFAULT 0,
                    verify_token VARCHAR(64),
                    reset_token VARCHAR(64),
                    reset_expires DATETIME,
                    avatar_color VARCHAR(20) DEFAULT '#FF9933',
                    state VARCHAR(50),
                    bio VARCHAR(200),
                    last_login DATETIME,
                    login_attempts TINYINT DEFAULT 0,
                    locked_until DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_username (username),
                    UNIQUE KEY uq_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # ── transactions ────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    step INT,
                    type VARCHAR(20),
                    amount_inr DECIMAL(18,2),
                    old_balance_orig DECIMAL(18,2),
                    new_balance_orig DECIMAL(18,2),
                    old_balance_dest DECIMAL(18,2),
                    new_balance_dest DECIMAL(18,2),
                    prediction ENUM('Fraud','Legitimate') NOT NULL,
                    confidence DECIMAL(5,2),
                    risk_score TINYINT UNSIGNED,
                    ip_address VARCHAR(45),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_user (user_id),
                    KEY idx_predict (prediction)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            conn.commit()
            print("✅ DB initialized")

    except Exception as e:
        print("❌ DB INIT FAILED:", e)