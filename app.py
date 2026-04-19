"""
app.py — Online Payment Fraud Detection v3.0
Developed by ANILREDDY | 9686809509
MySQL · Flask · ML · OTP 2FA · Security Hardened
"""
import os
import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, redirect, url_for, session
from config import Config

# ── SAFE IMPORTS (avoid crash if DB not available) ───────────
DB_ENABLED = True

try:
    from modules.db import init_db, mysql
except Exception as e:
    print("⚠️ DB module import failed:", e)
    DB_ENABLED = False

from modules.auth     import auth_bp
from modules.otp      import otp_bp
from modules.predict  import predict_bp
from modules.admin    import admin_bp
from modules.history  import history_bp
from modules.analytics import analytics_bp
from modules.alerts   import alerts_bp
from modules.export   import export_bp
from modules.search   import search_bp
from modules.heatmap  import heatmap_bp
from modules.receipt  import receipt_bp
from modules.users    import users_bp
from modules.settings import settings_bp

app = Flask(__name__)
app.config.from_object(Config)

# 🔐 Security configs
app.config["SECRET_KEY"] = "anigma_secure_key_2026"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = 1800
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ── Register all blueprints ─────────────────────────────────
for bp in [auth_bp, otp_bp, predict_bp, admin_bp, history_bp,
           analytics_bp, alerts_bp, export_bp, search_bp,
           heatmap_bp, receipt_bp, users_bp, settings_bp]:
    app.register_blueprint(bp)

# ── Init MySQL (SAFE MODE FOR RENDER) ───────────────────────
try:
    if DB_ENABLED:
        # 👉 Disable DB automatically on Render
        if os.environ.get("RENDER") or os.environ.get("DISABLE_DB") == "1":
            print("⚠️ Running in NO-DB mode (Render)")
            DB_ENABLED = False
        else:
            init_db(app)

            # 🔥 Test DB connection
            with app.app_context():
                conn = mysql.connection
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                print("✅ MySQL Connected Successfully")

except Exception as e:
    DB_ENABLED = False
    print("❌ MySQL Connection Failed:", e)
    print("⚠️ Switching to NO-DB mode")

# ── Root redirect ────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("predict.dashboard"))
    return redirect(url_for("auth.login"))

# 🔥 Health check (Render uses this sometimes)
@app.route("/health")
def health():
    return {
        "status": "ok",
        "db": "connected" if DB_ENABLED else "disabled"
    }

# 🔥 Global error handler
@app.errorhandler(Exception)
def handle_error(e):
    print("🔥 ERROR:", str(e))
    return "Something went wrong. Check logs.", 500

# ── Run server ───────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting OPFD Server...")
    if not DB_ENABLED:
        print("⚠️ Running without database (demo mode)")
    app.run(debug=True, host="0.0.0.0", port=5000)