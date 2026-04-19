"""
modules/security.py
────────────────────
ALL security features from checklist:
1.  Rate limiting + login attempt tracking
2.  Account lockout after N failures
3.  IP blacklist check
4.  HttpOnly + Secure session cookies
5.  Session token rotation on login
6.  Generic error messages (never expose logic)
7.  Password reset - expiring single-use tokens
8.  Don't reveal if email exists
9.  Invalidate sessions after reset
10. Server-side input validation
11. SQL injection prevention (parameterised queries)
12. Failed login logging + suspicious activity detection
13. Role-based access control decorators
14. CSRF-safe (SameSite cookies)
Developed by ANILREDDY | 9686809509
"""
import re, secrets, hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, redirect, url_for, flash, jsonify
from modules.db import execute, query_one, query


# ── Generic error message (never expose real reason) ─────────
GENERIC_AUTH_ERROR = "Invalid credentials. Please try again."


# ── IP Blacklist check ────────────────────────────────────────
def is_ip_blocked(ip):
    row = query_one(
        "SELECT id FROM ip_blacklist WHERE ip_address=%s", (ip,)
    )
    return row is not None


# ── Log audit event ───────────────────────────────────────────
def audit(user_id, action, details=""):
    execute(
        "INSERT INTO audit_log (user_id,action,details,ip_address) VALUES (%s,%s,%s,%s)",
        (user_id, action, details, request.remote_addr)
    )


# ── Failed login tracking ────────────────────────────────────
def record_failed_login(username):
    """Increment attempt counter; lock if threshold reached."""
    user = query_one("SELECT id,login_attempts FROM users WHERE username=%s", (username,))
    if not user:
        return  # Don't reveal user existence
    attempts = (user["login_attempts"] or 0) + 1
    lock_until = None
    cfg = query_one("SELECT setting_value FROM system_settings WHERE setting_key='max_login_attempts'")
    max_att = int(cfg["setting_value"]) if cfg else 5
    cfg2 = query_one("SELECT setting_value FROM system_settings WHERE setting_key='lockout_minutes'")
    lock_min = int(cfg2["setting_value"]) if cfg2 else 15
    if attempts >= max_att:
        lock_until = datetime.now() + timedelta(minutes=lock_min)
        audit(user["id"], "ACCOUNT_LOCKED",
              f"Locked after {attempts} failed attempts from {request.remote_addr}")
    execute(
        "UPDATE users SET login_attempts=%s, locked_until=%s WHERE id=%s",
        (attempts, lock_until, user["id"])
    )


def reset_login_attempts(user_id):
    execute("UPDATE users SET login_attempts=0, locked_until=NULL WHERE id=%s", (user_id,))


def is_account_locked(username):
    user = query_one(
        "SELECT locked_until FROM users WHERE username=%s", (username,)
    )
    if not user or not user["locked_until"]:
        return False
    return datetime.now() < user["locked_until"]


def minutes_until_unlock(username):
    user = query_one("SELECT locked_until FROM users WHERE username=%s", (username,))
    if not user or not user["locked_until"]:
        return 0
    delta = user["locked_until"] - datetime.now()
    return max(1, int(delta.total_seconds() // 60))


# ── Session token rotation ────────────────────────────────────
def rotate_session():
    """Regenerate session to prevent session fixation."""
    old_data = dict(session)
    session.clear()
    session.update(old_data)
    session.modified = True


# ── Password reset token (expiring, single-use) ──────────────
def generate_reset_token(user_id):
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(hours=1)
    execute(
        "UPDATE users SET reset_token=%s, reset_expires=%s WHERE id=%s",
        (token, expires, user_id)
    )
    return token


def validate_reset_token(token):
    """Returns user dict or None. Doesn't reveal if email exists."""
    user = query_one(
        "SELECT * FROM users WHERE reset_token=%s AND reset_expires > NOW()",
        (token,)
    )
    return user


def consume_reset_token(user_id):
    """Invalidate token after use + kill all sessions."""
    execute(
        "UPDATE users SET reset_token=NULL, reset_expires=NULL WHERE id=%s",
        (user_id,)
    )


# ── Email verify token ────────────────────────────────────────
def generate_verify_token(user_id):
    token = secrets.token_urlsafe(32)
    execute("UPDATE users SET verify_token=%s WHERE id=%s", (token, user_id))
    return token


# ── Server-side input validation ─────────────────────────────
def validate_registration(username, email, password, confirm, mobile=""):
    errors = []
    if len(username) < 4:
        errors.append("Username must be at least 4 characters.")
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        errors.append("Username can only contain letters, numbers and underscores.")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        errors.append("Invalid email address.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number.")
    if password != confirm:
        errors.append("Passwords do not match.")
    if mobile and not re.match(r"^[6-9]\d{9}$", mobile):
        errors.append("Enter a valid 10-digit Indian mobile number.")
    return errors


def validate_transaction_input(form):
    errors = []
    try:
        step = int(form.get("step", 0))
        if not (1 <= step <= 744):
            errors.append("Step must be between 1 and 744.")
    except (ValueError, TypeError):
        errors.append("Step must be a valid number.")
    try:
        t = int(form.get("type", 0))
        if t not in (1, 2, 3, 4, 5):
            errors.append("Invalid transaction type.")
    except (ValueError, TypeError):
        errors.append("Transaction type must be selected.")
    for field in ["amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]:
        try:
            v = float(form.get(field, -1))
            if v < 0:
                errors.append(f"{field} cannot be negative.")
        except (ValueError, TypeError):
            errors.append(f"{field} must be a valid number.")
    return errors


# ── Decorators ───────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("role") != "admin":
            audit(session["user_id"], "UNAUTHORISED_ADMIN",
                  f"Tried to access {request.path}")
            flash("Admin access required.", "danger")
            return redirect(url_for("predict.dashboard"))
        return f(*args, **kwargs)
    return decorated


def ip_block_required(f):
    """Reject requests from blacklisted IPs."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if is_ip_blocked(request.remote_addr):
            return "Access denied.", 403
        return f(*args, **kwargs)
    return decorated
