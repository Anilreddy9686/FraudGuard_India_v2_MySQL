import sys
import os

# Add the project root directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""modules/history.py"""
from flask import Blueprint, render_template, request, session
from modules.security import login_required
from modules.db import query, query_one

history_bp = Blueprint("history", __name__)

@history_bp.route("/history")
@login_required
def history():
    uid      = session["user_id"]
    is_admin = session.get("role") == "admin"
    page     = max(int(request.args.get("page", 1)), 1)
    per_page = 20
    offset   = (page - 1) * per_page
    filt     = request.args.get("filter", "all")

    # Build conditions and parameters safely
    conditions = []
    params = []

    if not is_admin:
        conditions.append("t.user_id = %s")
        params.append(uid)

    if filt == "fraud":
        conditions.append("t.prediction = 'Fraud'")
    elif filt == "legit":
        conditions.append("t.prediction = 'Legitimate'")

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # Get total count for pagination
    total_sql = f"SELECT COUNT(*) AS c FROM transactions t {where_clause}"
    total = query_one(total_sql, tuple(params))["c"]

    # Fetch rows with pagination
    # We add per_page and offset to the parameters list
    query_params = list(params)
    query_params.extend([per_page, offset])

    if is_admin:
        sql = f"""
            SELECT t.*, u.username 
            FROM transactions t 
            JOIN users u ON t.user_id = u.id 
            {where_clause} 
            ORDER BY t.created_at DESC 
            LIMIT %s OFFSET %s
        """
    else:
        sql = f"""
            SELECT t.* FROM transactions t 
            {where_clause} 
            ORDER BY t.created_at DESC 
            LIMIT %s OFFSET %s
        """

    rows = query(sql, tuple(query_params))

    pages = max((total + per_page - 1) // per_page, 1)
    
    return render_template("history.html", 
                           txns=rows, 
                           page=page, 
                           pages=pages,
                           total=total, 
                           filt=filt, 
                           is_admin=is_admin)