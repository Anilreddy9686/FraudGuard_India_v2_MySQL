"""modules/alerts.py"""
from flask import Blueprint, jsonify, render_template, session
from modules.security import login_required
from modules.db import execute, query, query_one

alerts_bp = Blueprint("alerts", __name__)

@alerts_bp.route("/alerts")
@login_required
def alerts():
    uid  = session["user_id"]
    rows = query("SELECT a.*, t.amount_inr, t.type AS txn_type FROM alerts a LEFT JOIN transactions t ON a.transaction_id=t.id WHERE a.user_id=%s ORDER BY a.created_at DESC", (uid,))
    execute("UPDATE alerts SET is_read=1 WHERE user_id=%s", (uid,))
    return render_template("alerts.html", alerts=rows)

@alerts_bp.route("/alerts/count")
@login_required
def alert_count():
    c = query_one("SELECT COUNT(*) AS c FROM alerts WHERE user_id=%s AND is_read=0", (session["user_id"],))["c"]
    return jsonify({"count": c})
