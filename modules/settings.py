import sys
import os

# Add the project root directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""modules/settings.py"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from modules.security import admin_required
from modules.db import execute, query

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/settings", methods=["GET","POST"])
@admin_required
def settings():
    if request.method == "POST":
        # List of keys to look for in the form submission
        config_keys = [
            "app_name", 
            "fraud_threshold", 
            "alert_email", 
            "otp_required", 
            "max_amount_alert", 
            "max_login_attempts", 
            "lockout_minutes"
        ]
        
        for k in config_keys:
            v = request.form.get(k, "").strip()
            # Update settings if they exist, or insert them if they don't
            execute("""
                INSERT INTO system_settings (setting_key, setting_value) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE setting_value = %s
            """, (k, v, v))
            
        flash("Settings saved.", "success")
        return redirect(url_for("settings.settings"))
    
    # Fetch current configuration from the database
    rows = query("SELECT * FROM system_settings")
    cfg = {r["setting_key"]: r["setting_value"] for r in rows}
    
    return render_template("settings.html", cfg=cfg)