import os
from datetime import timedelta

class Config:
    # 🔐 Core Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "opfd-anilreddy-secret-2025")
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)   # upgraded (more correct)

    # ── MySQL ──────────────────────────────────────────────
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")

    # 🔥 IMPORTANT FIX: use real password as fallback
    # (env var still takes priority if set)
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD") or "Anil@9686"

    MYSQL_DB = os.environ.get("MYSQL_DB", "opfd_india")
    MYSQL_CURSORCLASS = "DictCursor"

    # 🔥 ADD: MySQL connection stability
    MYSQL_AUTOCOMMIT = True
    MYSQL_PORT = 3306
    MYSQL_CONNECT_TIMEOUT = 10

    # ── Security ───────────────────────────────────────────
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # 🔥 ADD: Extra security flags
    SESSION_COOKIE_SECURE = False   # set True only if using HTTPS
    REMEMBER_COOKIE_HTTPONLY = True

    # 🔥 ADD: Session protection
    SESSION_PERMANENT = True

    # ── App Info ───────────────────────────────────────────
    APP_NAME  = "Online Payment Fraud Detection"
    DEVELOPER = "ANILREDDY"
    MOBILE    = "9686809509"
    VERSION   = "3.0.0"

    # 🔥 ADD: Debug toggle (auto)
    DEBUG = True if os.environ.get("FLASK_ENV") != "production" else False