"""modules/settings.py"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from modules.security import admin_required
from modules.db import execute, query

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/settings", methods=["GET","POST"])
@admin_required
def settings():
    if request.method=="POST":
        for k in ["app_name","fraud_threshold","alert_email","otp_required","max_amount_alert","max_login_attempts","lockout_minutes"]:
            v=request.form.get(k,"").strip()
            execute("INSERT INTO system_settings (setting_key,setting_value) VALUES (%s,%s) ON DUPLICATE KEY UPDATE setting_value=%s",(k,v,v))
        flash("Settings saved.","success")
        return redirect(url_for("settings.settings"))
    rows=query("SELECT * FROM system_settings")
    cfg={r["setting_key"]:r["setting_value"] for r in rows}
    return render_template("settings.html",cfg=cfg)
