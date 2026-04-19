"""modules/admin.py — Admin Panel"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from modules.security import admin_required, audit
from modules.db import execute, query, query_one
from werkzeug.security import generate_password_hash

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_required
def admin_dashboard():

    # 🔥 ADD: SAFE WRAPPER (NO CHANGE TO ORIGINAL CODE)
    try:
        users  = query("SELECT * FROM users ORDER BY created_at DESC")
        stats  = query_one("""
            SELECT COUNT(*) AS total_txns, SUM(prediction='Fraud') AS total_frauds,
                   COALESCE(SUM(amount_inr),0) AS total_volume,
                   COALESCE(SUM(CASE WHEN prediction='Fraud' THEN amount_inr ELSE 0 END),0) AS fraud_volume
            FROM transactions
        """)
        recent = query("""
            SELECT t.*, u.username FROM transactions t JOIN users u ON t.user_id=u.id
            ORDER BY t.created_at DESC LIMIT 25
        """)
        audit_rows = query("""
            SELECT a.*, u.username FROM audit_log a LEFT JOIN users u ON a.user_id=u.id
            ORDER BY a.created_at DESC LIMIT 40
        """)
        blacklist = query("SELECT * FROM ip_blacklist ORDER BY created_at DESC")

        return render_template("admin.html", users=users, stats=stats,
                               recent=recent, audit=audit_rows, blacklist=blacklist)

    except Exception as e:
        print("🔥 ADMIN DASHBOARD ERROR:", e)

        # 🔥 ADD: DEMO DATA (NO DB MODE)
        demo_users = [{
            "id": 1,
            "username": "admin",
            "email": "admin@test.com",
            "role": "admin",
            "is_active": 1,
            "created_at": "2026-01-01"
        }]

        demo_stats = {
            "total_txns": 20,
            "total_frauds": 5,
            "total_volume": 100000,
            "fraud_volume": 30000
        }

        demo_recent = [{
            "id": 1,
            "username": "admin",
            "type": "TRANSFER",
            "amount_inr": 5000,
            "prediction": "Legitimate",
            "created_at": "2026-01-01 10:00"
        }]

        demo_audit = [{
            "id": 1,
            "username": "admin",
            "action": "LOGIN",
            "created_at": "2026-01-01 09:00"
        }]

        demo_blacklist = []

        return render_template(
            "admin.html",
            users=demo_users,
            stats=demo_stats,
            recent=demo_recent,
            audit=demo_audit,
            blacklist=demo_blacklist,
            demo_mode=True
        )


@admin_bp.route("/toggle/<int:uid>", methods=["POST"])
@admin_required
def toggle_user(uid):
    if uid == session["user_id"]:
        flash("Cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    # 🔥 ADD SAFE WRAPPER
    try:
        user = query_one("SELECT is_active,username FROM users WHERE id=%s", (uid,))
        if user:
            new = 0 if user["is_active"] else 1
            execute("UPDATE users SET is_active=%s WHERE id=%s", (new, uid))
            audit(session["user_id"], "TOGGLE_USER", f"{'Activated' if new else 'Deactivated'} {user['username']}")
            flash(f"User {'activated' if new else 'deactivated'}.", "success")
    except Exception as e:
        print("🔥 TOGGLE ERROR:", e)

    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/promote/<int:uid>", methods=["POST"])
@admin_required
def promote(uid):
    try:
        execute("UPDATE users SET role='admin' WHERE id=%s", (uid,))
        flash("User promoted to Admin.", "success")
    except Exception as e:
        print("🔥 PROMOTE ERROR:", e)
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/demote/<int:uid>", methods=["POST"])
@admin_required
def demote(uid):
    if uid == session["user_id"]:
        flash("Cannot demote yourself.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    try:
        execute("UPDATE users SET role='user' WHERE id=%s", (uid,))
        flash("User demoted.", "info")
    except Exception as e:
        print("🔥 DEMOTE ERROR:", e)

    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/delete_txn/<int:tid>", methods=["POST"])
@admin_required
def delete_txn(tid):
    try:
        execute("DELETE FROM transactions WHERE id=%s", (tid,))
        flash("Transaction deleted.", "info")
    except Exception as e:
        print("🔥 DELETE TXN ERROR:", e)
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/reset_password/<int:uid>", methods=["POST"])
@admin_required
def reset_password(uid):
    new_pw = request.form.get("new_password", "")
    if len(new_pw) < 8:
        flash("Password must be at least 8 characters.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    try:
        execute("UPDATE users SET password_hash=%s WHERE id=%s",
                (generate_password_hash(new_pw), uid))
        audit(session["user_id"], "ADMIN_RESET_PW", f"Reset password for user_id={uid}")
        flash("Password reset.", "success")
    except Exception as e:
        print("🔥 RESET PW ERROR:", e)

    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/delete_user/<int:uid>", methods=["POST"])
@admin_required
def delete_user(uid):
    if uid == session["user_id"]:
        flash("Cannot delete your own account.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    try:
        user = query_one("SELECT username FROM users WHERE id=%s", (uid,))
        if user:
            execute("DELETE FROM users WHERE id=%s", (uid,))
            audit(session["user_id"], "DELETE_USER", f"Deleted: {user['username']}")
            flash(f"User '{user['username']}' deleted.", "success")
    except Exception as e:
        print("🔥 DELETE USER ERROR:", e)

    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/block_ip", methods=["POST"])
@admin_required
def block_ip():
    ip     = request.form.get("ip_address", "").strip()
    reason = request.form.get("reason", "Manual block").strip()

    if ip:
        try:
            execute("INSERT IGNORE INTO ip_blacklist (ip_address,reason,blocked_by) VALUES (%s,%s,%s)",
                    (ip, reason, session["user_id"]))
            audit(session["user_id"], "IP_BLOCKED", f"Blocked IP: {ip}")
            flash(f"IP {ip} blocked.", "success")
        except Exception as e:
            print("🔥 BLOCK IP ERROR:", e)

    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/unblock_ip/<int:bid>", methods=["POST"])
@admin_required
def unblock_ip(bid):
    try:
        row = query_one("SELECT ip_address FROM ip_blacklist WHERE id=%s", (bid,))
        if row:
            execute("DELETE FROM ip_blacklist WHERE id=%s", (bid,))
            audit(session["user_id"], "IP_UNBLOCKED", f"Unblocked IP: {row['ip_address']}")
            flash("IP unblocked.", "success")
    except Exception as e:
        print("🔥 UNBLOCK IP ERROR:", e)

    return redirect(url_for("admin.admin_dashboard"))