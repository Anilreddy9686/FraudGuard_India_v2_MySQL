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
    # 🔥 SAFE WRAPPER: Prevents the entire application from crashing on DB errors
    try:
        print("📊 Analytics route accessed")

        uid      = session.get("user_id")
        is_admin = session.get("role") == "admin"

        print(f"👤 User ID: {uid} | Admin: {is_admin}")

        # ── Data Scope Logic ──────────────────────────────────────────
        if is_admin:
            where_clause = ""
            params = None   # ✅ safer than empty tuple
        else:
            where_clause = "WHERE user_id = %s"
            params = (uid,)

        # 🔧 SAFE QUERY WRAPPER (prevents formatting crashes)
        def safe_query(sql, params=None):
            try:
                if params:
                    return query(sql, params) or []
                else:
                    return query(sql) or []
            except Exception as e:
                print("⚠️ Query failed:", e)
                return []

        # 1. Monthly Trend
        monthly = safe_query(f"""
            SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS month, 
                   COUNT(*) AS total, 
                   SUM(CASE WHEN LOWER(prediction)='fraud' THEN 1 ELSE 0 END) AS frauds, 
                   COALESCE(SUM(amount_inr), 0) AS volume 
            FROM transactions 
            {where_clause} 
            GROUP BY month 
            ORDER BY month DESC LIMIT 12
        """, params)

        print("📈 Monthly Data:", monthly)

        # 2. Transactions by Type
        by_type = safe_query(f"""
            SELECT type, 
                   COUNT(*) AS total, 
                   SUM(CASE WHEN LOWER(prediction)='fraud' THEN 1 ELSE 0 END) AS frauds, 
                   COALESCE(AVG(amount_inr), 0) AS avg_amount 
            FROM transactions 
            {where_clause} 
            GROUP BY type
        """, params)

        # 3. Risk Distribution
        risk_dist = safe_query(f"""
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
        """, params)

        # 4. Top Users (Admin-only Insights)
        top_users = []
        if is_admin:
            top_users = safe_query("""
                SELECT u.username, 
                       COUNT(*) AS txns, 
                       SUM(CASE WHEN LOWER(t.prediction)='fraud' THEN 1 ELSE 0 END) AS frauds, 
                       COALESCE(SUM(t.amount_inr), 0) AS volume 
                FROM transactions t 
                JOIN users u ON t.user_id = u.id 
                GROUP BY u.username 
                ORDER BY frauds DESC LIMIT 10
            """)

        # 🔥 DEMO FALLBACK
        if not monthly and not by_type and not risk_dist:
            print("⚠️ No analytics data in DB → Loading Demo Mode")

            demo_monthly = [{
                "month": "2026-04",
                "total": 150,
                "frauds": 12,
                "volume": 850000.00
            }]

            demo_by_type = [
                {"type": "TRANSFER", "total": 60, "frauds": 7, "avg_amount": 15000.00},
                {"type": "PAYMENT", "total": 90, "frauds": 5, "avg_amount": 4200.00}
            ]

            demo_risk = [
                {"band": "Low (0-29)", "cnt": 110},
                {"band": "Medium (30-59)", "cnt": 25},
                {"band": "High (60-79)", "cnt": 10},
                {"band": "Critical (80+)", "cnt": 5},
            ]

            demo_top = [{
                "username": "anil_reddy",
                "txns": 45,
                "frauds": 3,
                "volume": 320000.00
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

        # ── Normal Rendering ──────────────────────────────────────────
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
        # 🔥 HARD FAIL-SAFE
        print("🔥 CRITICAL ANALYTICS ERROR:", e)

        return render_template(
            "analytics.html",
            monthly=[{"month": "Error", "total": 0, "frauds": 0, "volume": 0}],
            by_type=[{"type": "Error", "total": 0, "frauds": 0, "avg_amount": 0}],
            risk_dist=[{"band": "System Offline", "cnt": 0}],
            top_users=[],
            is_admin=False,
            demo_mode=True,
            error_message=f"Database synchronization error: {str(e)}"
        )