"""
modules/db.py
MySQL connection + auto-create all tables
Developed by ANILREDDY | 9686809509
"""

# 🔥 ADD: Safe import fallback (Windows fix)
try:
    from flask_mysqldb import MySQL
except ModuleNotFoundError:
    import pymysql
    pymysql.install_as_MySQLdb()
    from flask_mysqldb import MySQL

mysql = MySQL()


def get_cursor():
    from flask import g
    if "db_conn" not in g:
        g.db_conn = mysql.connection
    return g.db_conn.cursor()


def query(sql, args=()):
    cur = get_cursor()
    cur.execute(sql, args)
    return cur.fetchall()


def query_one(sql, args=()):
    cur = get_cursor()
    cur.execute(sql, args)
    return cur.fetchone()


def execute(sql, args=()):
    conn = mysql.connection
    cur  = conn.cursor()
    cur.execute(sql, args)
    conn.commit()
    return cur.lastrowid


def init_db(app):
    mysql.init_app(app)
    with app.app_context():
        conn = mysql.connection
        cur  = conn.cursor()

        # ── users ──────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                username         VARCHAR(60)  NOT NULL,
                email            VARCHAR(120) NOT NULL,
                password_hash    VARCHAR(256) NOT NULL,
                full_name        VARCHAR(120),
                mobile           VARCHAR(12),
                role             ENUM('user','admin') DEFAULT 'user',
                is_active        TINYINT(1) DEFAULT 1,
                otp_enabled      TINYINT(1) DEFAULT 0,
                email_verified   TINYINT(1) DEFAULT 0,
                verify_token     VARCHAR(64),
                reset_token      VARCHAR(64),
                reset_expires    DATETIME,
                avatar_color     VARCHAR(20) DEFAULT '#FF9933',
                state            VARCHAR(50),
                bio              VARCHAR(200),
                last_login       DATETIME,
                login_attempts   TINYINT DEFAULT 0,
                locked_until     DATETIME,
                created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_username (username),
                UNIQUE KEY uq_email    (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── transactions ────────────────────────────────────
        cur.execute("""
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
                KEY idx_user    (user_id),
                KEY idx_predict (prediction),
                CONSTRAINT fk_txn_user FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── alerts ──────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                user_id        INT NOT NULL,
                transaction_id INT,
                alert_type     VARCHAR(40),
                message        TEXT,
                is_read        TINYINT(1) DEFAULT 0,
                created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
                KEY idx_unread (user_id, is_read),
                CONSTRAINT fk_alert_user FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_alert_txn  FOREIGN KEY (transaction_id)
                    REFERENCES transactions(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── audit_log ───────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                user_id    INT,
                action     VARCHAR(60),
                details    TEXT,
                ip_address VARCHAR(45),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                KEY idx_user   (user_id),
                KEY idx_action (action)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── otp_tokens ──────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS otp_tokens (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                user_id    INT NOT NULL,
                otp_code   VARCHAR(6) NOT NULL,
                purpose    VARCHAR(30) DEFAULT 'login',
                is_used    TINYINT(1) DEFAULT 0,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_otp_user FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── system_settings ─────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                setting_key   VARCHAR(60) UNIQUE NOT NULL,
                setting_value TEXT,
                updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── ip_blacklist ─────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ip_blacklist (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                ip_address VARCHAR(45) NOT NULL UNIQUE,
                reason     VARCHAR(200),
                blocked_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        conn.commit()

        # Seed settings
        defaults = [
            ('app_name',         'Online Payment Fraud Detection'),
            ('developer',        'ANILREDDY'),
            ('mobile',           '9686809509'),
            ('fraud_threshold',  '60'),
            ('alert_email',      'anilreddy@opfd.in'),
            ('otp_required',     '0'),
            ('max_amount_alert', '5000000'),
            ('max_login_attempts','5'),
            ('lockout_minutes',  '15'),
        ]
        for k, v in defaults:
            cur.execute(
                "INSERT IGNORE INTO system_settings (setting_key,setting_value) VALUES (%s,%s)",
                (k, v)
            )

        # Seed admin
        cur.execute("SELECT id FROM users WHERE username='admin'")
        if not cur.fetchone():
            from werkzeug.security import generate_password_hash
            cur.execute("""
                INSERT INTO users
                  (username,email,password_hash,full_name,role,email_verified)
                VALUES (%s,%s,%s,%s,'admin',1)""",
                ("admin","anilreddy@opfd.in",
                 generate_password_hash("Admin@123"), "ANILREDDY"))

        conn.commit()
        print("✅ opfd_india DB ready — admin / Admin@123")