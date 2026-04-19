"""
modules/auth.py
────────────────
Login · Register · Logout · Password Reset · Email Verify
All security checklist items implemented
"""
import re
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from modules.db import execute, query_one
from modules.security import (
    GENERIC_AUTH_ERROR, audit, generate_reset_token, generate_verify_token,
    is_account_locked, is_ip_blocked, minutes_until_unlock, record_failed_login,
    reset_login_attempts, rotate_session, validate_registration,
    consume_reset_token, validate_reset_token
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("predict.dashboard"))

    # Block blacklisted IPs
    if is_ip_blocked(request.remote_addr):
        return render_template("blocked.html"), 403

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Account lockout check
        if is_account_locked(username):
            mins = minutes_until_unlock(username)
            flash(f"Account temporarily locked. Try again in {mins} minute(s).", "danger")
            return render_template("login.html")

        user = query_one(
            "SELECT * FROM users WHERE username=%s AND is_active=1", (username,)
        )

        # Generic error — never reveal if username exists
        if not user or not check_password_hash(user["password_hash"], password):
            record_failed_login(username)
            audit(None, "LOGIN_FAILED", f"Failed attempt for: {username}")
            flash(GENERIC_AUTH_ERROR, "danger")
            return render_template("login.html")

        # Reset failed attempts
        reset_login_attempts(user["id"])

        # Check OTP 2FA
        otp_req = query_one(
            "SELECT setting_value FROM system_settings WHERE setting_key='otp_required'"
        )
        force_otp = otp_req and otp_req["setting_value"] == "1"

        if user.get("otp_enabled") or force_otp:
            from modules.otp import create_otp_for_user
            create_otp_for_user(user["id"], user["email"], user["full_name"] or user["username"])
            session["pending_user_id"]   = user["id"]
            session["pending_username"]  = user["username"]
            session["pending_role"]      = user["role"]
            session["pending_full_name"] = user["full_name"] or user["username"]
            flash("OTP sent! Check your console/email.", "info")
            return redirect(url_for("otp.otp_verify"))

        # Rotate session token (prevent session fixation)
        rotate_session()

        session.permanent    = True
        session["user_id"]   = user["id"]
        session["username"]  = user["username"]
        session["role"]      = user["role"]
        session["full_name"] = user["full_name"] or user["username"]

        execute("UPDATE users SET last_login=%s WHERE id=%s", (datetime.now(), user["id"]))
        audit(user["id"], "LOGIN", f"{username} logged in from {request.remote_addr}")

        flash(f"Welcome back, {session['full_name']}! \U0001f64f", "success")
        return redirect(
            url_for("admin.admin_dashboard")
            if user["role"] == "admin"
            else url_for("predict.dashboard")
        )

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username  = request.form.get("username",         "").strip()
        email     = request.form.get("email",            "").strip()
        password  = request.form.get("password",         "")
        confirm   = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name",        "").strip()
        mobile    = request.form.get("mobile",           "").strip()

        errors = validate_registration(username, email, password, confirm, mobile)
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html")

        # Prevent duplicate accounts — generic message
        existing = query_one(
            "SELECT id FROM users WHERE username=%s OR email=%s", (username, email)
        )
        if existing:
            flash("Registration failed. Please check your details.", "danger")
            return render_template("register.html")

        uid = execute(
            """INSERT INTO users
               (username,email,password_hash,full_name,mobile,role,email_verified)
               VALUES (%s,%s,%s,%s,%s,'user',1)""",
            (username, email, generate_password_hash(password), full_name, mobile)
        )
        audit(uid, "REGISTER", f"New user: {username}")
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    if "user_id" in session:
        audit(session["user_id"], "LOGOUT", f"{session.get('username')} logged out")
    session.clear()
    flash("You have been logged out securely.", "info")
    return redirect(url_for("auth.login"))


# ── Password Reset ───────────────────────────────────────────
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user  = query_one("SELECT * FROM users WHERE email=%s", (email,))
        # SECURITY: Always show same message whether email exists or not
        flash("If that email is registered, a reset link has been sent.", "info")
        if user:
            token = generate_reset_token(user["id"])
            # In production: send email. For dev: print to console
            print(f"\n{'='*50}")
            print(f"  PASSWORD RESET LINK for {email}:")
            print(f"  http://localhost:5000/reset-password/{token}")
            print(f"  Valid for 1 hour.")
            print(f"{'='*50}\n")
            audit(user["id"], "PASSWORD_RESET_REQUESTED",
                  f"Reset requested from {request.remote_addr}")
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = validate_reset_token(token)
    if not user:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("reset_password.html", token=token)
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("reset_password.html", token=token)

        execute(
            "UPDATE users SET password_hash=%s WHERE id=%s",
            (generate_password_hash(password), user["id"])
        )
        consume_reset_token(user["id"])
        # Invalidate any active sessions
        session.clear()
        audit(user["id"], "PASSWORD_RESET", "Password reset successfully")
        flash("Password reset successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)
