import sys
import os

# Add the project root directory to the python path to resolve 'modules' imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
modules/analytics.py
────────────────────
Handles data visualization logic for trends, risk, and fraud distribution.
Includes robust error handling and demo-data fallback.
Developed by ANILREDDY | 9686809509
"""
from flask import Blueprint, render_template, session
from modules.security import login_required
from modules.db import query

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics")
@login_required
def analytics():
    # 🔥 SAFE WRAPPER
    try:
        uid      = session.get("user_id")
        is_admin = session.get("role") == "admin"
        
        # Use tuple-based arguments for the WHERE clause to keep it clean
        if is_admin:
            where_clause = ""
            params = ()
        else:
            where_clause = "WHERE user_id = %s"
            params = (uid,)

        # 1. Monthly Trend
        # Note the double %% in DATE_FORMAT for Flask-MySQLdb escaping
        monthly = query(f"""
            SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS month, 
                   COUNT(*) AS total, 
                   SUM(CASE WHEN LOWER(prediction)='fraud' THEN 1 ELSE 0 END) AS frauds, 
                   COALESCE(SUM(amount_inr), 0) AS volume 
            FROM transactions 
            {where_clause} 
            GROUP BY month 
            ORDER BY month DESC LIMIT 12
        """, params) or []

        # 2. Transactions by Type
        by_type = query(f"""
            SELECT type, 
                   COUNT(*) AS total, 
                   SUM(CASE WHEN LOWER(prediction)='fraud' THEN 1 ELSE 0 END) AS frauds, 
                   COALESCE(AVG(amount_inr), 0) AS avg_amount 
            FROM transactions 
            {where_clause} 
            GROUP BY type
        """, params) or []

        # 3. Risk Distribution
        risk_dist = query(f"""
            SELECT CASE 
                WHEN risk_score < 30 THEN 'Low (0-29)' 
                WHEN risk_score < 60 THEN 'Medium (30-59)' 
                WHEN risk_score < 80 THEN 'High (60-79)' 
                ELSE 'Critical (80+)' 
            END AS band, 
            COUNT(*) AS cnt 
            FROM transactions 
            {where_clause} 
            GROUP BY band 
            ORDER BY MIN(risk_score)
        """, params) or []

        # 4. Top Users (Admin Only)
        top_users = []
        if is_admin:
            top_users = query("""
                SELECT u.username, 
                       COUNT(*) AS txns, 
                   SUM(CASE WHEN LOWER(t.prediction)='fraud' THEN 1 ELSE 0 END) AS frauds, 
                       COALESCE(SUM(t.amount_inr), 0) AS volume 
                FROM transactions t 
                JOIN users u ON t.user_id = u.id 
                GROUP BY u.username 
                ORDER BY frauds DESC LIMIT 10
            """) or []

        # 🔥 DEMO FALLBACK IF NO DATA FOUND IN DATABASE
        if not monthly and not by_type and not risk_dist:
            print("⚠️ No analytics data in DB → Loading Demo Mode")

            demo_monthly = [{
                "month": "2026-04",
                "total": 120,
                "frauds": 15,
                "volume": 750000.00
            }]

            demo_by_type = [{
                "type": "TRANSFER",
                "total": 45,
                "frauds": 8,
                "avg_amount": 12500.50
            }, {
                "type": "PAYMENT",
                "total": 75,
                "frauds": 7,
                "avg_amount": 3200.75
            }]

            demo_risk = [
                {"band": "Low (0-29)", "cnt": 85},
                {"band": "Medium (30-59)", "cnt": 20},
                {"band": "High (60-79)", "cnt": 10},
                {"band": "Critical (80+)", "cnt": 5},
            ]

            demo_top = [{
                "username": "anil_reddy",
                "txns": 50,
                "frauds": 2,
                "volume": 250000.00
            }]

            return render_template(
                "analytics.html",
                monthly=demo_monthly,
                by_type=demo_by_type,
                risk_dist=demo_risk,
                top_users=demo_top,
                is_admin=True,
                demo_mode=True
            )

        # Normal Response
        return render_template(
            "analytics.html", 
            monthly=monthly, 
            by_type=by_type,
            risk_dist=risk_dist, 
            top_users=top_users, 
            is_admin=is_admin,
            demo_mode=False
        )

    except Exception as e:
        print("🔥 CRITICAL ANALYTICS ERROR:", e)

        # 🔥 HARD FALLBACK (Ensures page renders even if DB connection is lost)
        return render_template(
            "analytics.html",
            monthly=[{"month": "Error", "total": 0, "frauds": 0, "volume": 0}],
            by_type=[{"type": "Error", "total": 0, "frauds": 0, "avg_amount": 0}],
            risk_dist=[{"band": "No Data", "cnt": 0}],
            top_users=[],
            is_admin=False,
            demo_mode=True,
            error_message="System encountered an error while loading data."
        )