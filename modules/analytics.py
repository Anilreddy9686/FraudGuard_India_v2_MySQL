"""modules/analytics.py"""
from flask import Blueprint, render_template, session
from modules.security import login_required
from modules.db import query

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics")
@login_required
def analytics():
    uid      = session["user_id"]
    is_admin = session.get("role") == "admin"

    where_clause = "" if is_admin else f"WHERE user_id={uid}"

    # 🔥 FIX: %% instead of % (VERY IMPORTANT)
    monthly = query(f"""
        SELECT 
            DATE_FORMAT(created_at,'%%Y-%%m') AS month,
            COUNT(*) AS total,
            SUM(prediction='Fraud') AS frauds,
            COALESCE(SUM(amount_inr),0) AS volume
        FROM transactions
        {where_clause}
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)

    by_type = query(f"""
        SELECT 
            type,
            COUNT(*) AS total,
            SUM(prediction='Fraud') AS frauds,
            COALESCE(AVG(amount_inr),0) AS avg_amount
        FROM transactions
        {where_clause}
        GROUP BY type
    """)

    risk_dist = query(f"""
        SELECT 
            CASE 
                WHEN risk_score < 30 THEN 'Low (0-29)'
                WHEN risk_score < 60 THEN 'Medium (30-59)'
                WHEN risk_score < 80 THEN 'High (60-79)'
                ELSE 'Critical (80+)'
            END AS band,
            COUNT(*) AS cnt
        FROM transactions
        {where_clause}
        GROUP BY band
        ORDER BY cnt DESC
    """)

    top_users = query("""
        SELECT 
            u.username,
            COUNT(*) AS txns,
            SUM(t.prediction='Fraud') AS frauds,
            COALESCE(SUM(t.amount_inr),0) AS volume
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        GROUP BY u.username
        ORDER BY frauds DESC
        LIMIT 10
    """) if is_admin else []

    return render_template(
        "analytics.html",
        monthly=monthly,
        by_type=by_type,
        risk_dist=risk_dist,
        top_users=top_users,
        is_admin=is_admin
    )