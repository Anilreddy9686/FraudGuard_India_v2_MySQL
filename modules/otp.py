"""modules/otp.py — 6-digit OTP 2FA"""
import random, string
from datetime import datetime, timedelta
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from modules.db import execute, query_one
from modules.security import audit, rotate_session

otp_bp = Blueprint("otp", __name__)


def generate_otp():
    return "".join(random.choices(string.digits, k=6))


def create_otp_for_user(user_id, email, name):
    execute("UPDATE otp_tokens SET is_used=1 WHERE user_id=%s AND purpose='login'", (user_id,))
    otp     = generate_otp()
    expires = datetime.now() + timedelta(minutes=5)
    execute(
        "INSERT INTO otp_tokens (user_id,otp_code,purpose,expires_at) VALUES (%s,%s,'login',%s)",
        (user_id, otp, expires)
    )
    print(f"\n{'='*50}\n  OTP for {name} ({email}): {otp}\n  Valid 5 minutes.\n{'='*50}\n")
    return otp


@otp_bp.route("/otp-verify", methods=["GET", "POST"])
def otp_verify():
    if "pending_user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        entered = request.form.get("otp_code", "").strip()
        uid     = session["pending_user_id"]
        token   = query_one("""
            SELECT * FROM otp_tokens
            WHERE user_id=%s AND purpose='login' AND is_used=0 AND expires_at>NOW()
            ORDER BY created_at DESC LIMIT 1
        """, (uid,))

        if token and token["otp_code"] == entered:
            execute("UPDATE otp_tokens SET is_used=1 WHERE id=%s", (token["id"],))
            rotate_session()
            session["user_id"]   = session.pop("pending_user_id")
            session["username"]  = session.pop("pending_username")
            session["role"]      = session.pop("pending_role")
            session["full_name"] = session.pop("pending_full_name")
            session.permanent    = True
            execute("UPDATE users SET last_login=%s WHERE id=%s", (datetime.now(), session["user_id"]))
            audit(session["user_id"], "LOGIN_OTP", "Passed OTP verification")
            flash(f"Welcome, {session['full_name']}! \U0001f64f", "success")
            return redirect(
                url_for("admin.admin_dashboard") if session["role"] == "admin"
                else url_for("predict.dashboard")
            )
        flash("Invalid or expired OTP.", "danger")

    if request.args.get("resend"):
        uid  = session.get("pending_user_id")
        user = query_one("SELECT * FROM users WHERE id=%s", (uid,))
        if user:
            create_otp_for_user(uid, user["email"], user["full_name"] or user["username"])
            flash("New OTP sent!", "info")

    return render_template("otp_verify.html")
