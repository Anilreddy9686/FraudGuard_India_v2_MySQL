"""
app.py — Online Payment Fraud Detection v3.0
Developed by ANILREDDY | 9686809509
MySQL · Flask · ML · OTP 2FA · Security Hardened
"""
import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, redirect, url_for, session
from config import Config

from modules.db       import init_db, mysql
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

# 🔐 ADD: Secret key (required for session security)
app.config["SECRET_KEY"] = "anigma_secure_key_2026"

# 🔐 ADD: Extra security headers
app.config["SESSION_COOKIE_SECURE"] = False  # True only in HTTPS
app.config["PERMANENT_SESSION_LIFETIME"] = 1800  # 30 min timeout

# ── Security: HttpOnly + SameSite cookies ───────────────────
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ── Register all blueprints ─────────────────────────────────
for bp in [auth_bp, otp_bp, predict_bp, admin_bp, history_bp,
           analytics_bp, alerts_bp, export_bp, search_bp,
           heatmap_bp, receipt_bp, users_bp, settings_bp]:
    app.register_blueprint(bp)

# ── Init MySQL ───────────────────────────────────────────────
init_db(app)

# 🔥 ADD: Test DB connection on startup
try:
    with app.app_context():
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        print("✅ MySQL Connected Successfully")
except Exception as e:
    print("❌ MySQL Connection Failed:", e)

# ── Root redirect ────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("predict.dashboard"))
    return redirect(url_for("auth.login"))

# 🔥 ADD: Global error handler (prevents crash UI)
@app.errorhandler(Exception)
def handle_error(e):
    print("🔥 ERROR:", str(e))
    return "Something went wrong. Check terminal.", 500

if __name__ == "__main__":
    print("🚀 Starting OPFD Server...")
    app.run(debug=True, host="0.0.0.0", port=5000)