"""modules/users.py — All Users + My Profile"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from modules.security import admin_required, login_required, audit
from modules.db import execute, query, query_one

users_bp = Blueprint("users", __name__)
INDIAN_STATES=["Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal","Delhi","Jammu & Kashmir","Ladakh","Puducherry"]

@users_bp.route("/users")
@admin_required
def all_users():
    users = query("SELECT u.*,COUNT(t.id) AS txn_count,SUM(t.prediction='Fraud') AS fraud_count,COALESCE(SUM(t.amount_inr),0) AS total_volume FROM users u LEFT JOIN transactions t ON u.id=t.user_id GROUP BY u.id ORDER BY u.created_at DESC")
    stats = query_one("SELECT COUNT(*) AS total,SUM(role='admin') AS admins,SUM(is_active=1) AS active,SUM(is_active=0) AS inactive FROM users")
    return render_template("users_all.html", users=users, stats=stats, states=INDIAN_STATES)

@users_bp.route("/users/delete/<int:uid>", methods=["POST"])
@admin_required
def delete_user(uid):
    if uid==session["user_id"]: flash("Cannot delete yourself.","danger"); return redirect(url_for("users.all_users"))
    u=query_one("SELECT username FROM users WHERE id=%s",(uid,))
    if u:
        execute("DELETE FROM users WHERE id=%s",(uid,))
        audit(session["user_id"],"DELETE_USER",f"Deleted: {u['username']}")
        flash(f"User '{u['username']}' deleted.","success")
    return redirect(url_for("users.all_users"))

@users_bp.route("/users/reset_password/<int:uid>", methods=["POST"])
@admin_required
def admin_reset_password(uid):
    pw=request.form.get("new_password","")
    if len(pw)<8: flash("Min 8 characters.","danger"); return redirect(url_for("users.all_users"))
    execute("UPDATE users SET password_hash=%s WHERE id=%s",(generate_password_hash(pw),uid))
    flash("Password reset.","success")
    return redirect(url_for("users.all_users"))

@users_bp.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    uid  = session["user_id"]
    user = query_one("SELECT * FROM users WHERE id=%s",(uid,))
    if request.method=="POST":
        action=request.form.get("action")
        if action=="update_profile":
            execute("UPDATE users SET full_name=%s,mobile=%s,state=%s,bio=%s WHERE id=%s",
                    (request.form.get("full_name",""),request.form.get("mobile",""),
                     request.form.get("state",""),request.form.get("bio",""),uid))
            session["full_name"]=request.form.get("full_name","")
            flash("Profile updated.","success")
        elif action=="change_password":
            curr=request.form.get("current_password","")
            nw=request.form.get("new_password","")
            conf=request.form.get("confirm_password","")
            if not check_password_hash(user["password_hash"],curr): flash("Current password incorrect.","danger")
            elif len(nw)<8: flash("Min 8 characters.","danger")
            elif nw!=conf: flash("Passwords don't match.","danger")
            else:
                execute("UPDATE users SET password_hash=%s WHERE id=%s",(generate_password_hash(nw),uid))
                audit(uid,"CHANGE_PASSWORD","User changed own password")
                flash("Password changed.","success")
        elif action=="toggle_otp":
            cur=user.get("otp_enabled",0)
            execute("UPDATE users SET otp_enabled=%s WHERE id=%s",(0 if cur else 1,uid))
            flash(f"OTP {'disabled' if cur else 'enabled'}.","success")
        return redirect(url_for("users.profile"))
    stats=query_one("SELECT COUNT(*) AS total,SUM(prediction='Fraud') AS frauds,COALESCE(SUM(amount_inr),0) AS volume FROM transactions WHERE user_id=%s",(uid,))
    recent_audit=query("SELECT * FROM audit_log WHERE user_id=%s ORDER BY created_at DESC LIMIT 10",(uid,))
    return render_template("profile.html",user=user,stats=stats,recent_audit=recent_audit,states=INDIAN_STATES)
