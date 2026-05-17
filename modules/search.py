import sys
import os

# Add the project root directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""modules/search.py — Advanced Search & Filter"""
from flask import Blueprint, render_template, request, session, jsonify
from modules.security import login_required
from modules.db import query, query_one

search_bp = Blueprint("search", __name__)
TXN_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

@search_bp.route("/search")
@login_required
def search():
    return render_template("search.html", 
                           txn_types=TXN_TYPES, 
                           is_admin=session.get("role") == "admin")

@search_bp.route("/search/results")
@login_required
def search_results():
    uid      = session["user_id"]
    is_admin = session.get("role") == "admin"
    page     = max(int(request.args.get("page", 1)), 1)
    per_page = 25
    offset   = (page - 1) * per_page
    
    conditions = []
    args = []

    # Access control: users can only search their own data
    if not is_admin:
        conditions.append("t.user_id = %s")
        args.append(uid)

    # General keyword search
    kw = request.args.get("q", "").strip()
    if kw:
        conditions.append("(t.type LIKE %s OR t.prediction LIKE %s)")
        args.extend([f"%{kw}%", f"%{kw}%"])

    # Specific filters
    tt = request.args.get("type", "")
    if tt in TXN_TYPES:
        conditions.append("t.type = %s")
        args.append(tt)

    pred = request.args.get("prediction", "")
    if pred in ("Fraud", "Legitimate"):
        conditions.append("t.prediction = %s")
        args.append(pred)

    # Numeric filters
    filters = [
        ("amt_min", "t.amount_inr >="),
        ("amt_max", "t.amount_inr <="),
        ("risk_min", "t.risk_score >=")
    ]
    for field, col in filters:
        try:
            val = request.args.get(field, "").strip()
            if val:
                v = float(val)
                conditions.append(f"{col} %s")
                args.append(v)
        except (ValueError, TypeError):
            pass

    # Date filters
    df = request.args.get("date_from", "")
    dt = request.args.get("date_to", "")
    if df:
        conditions.append("DATE(t.created_at) >= %s")
        args.append(df)
    if dt:
        conditions.append("DATE(t.created_at) <= %s")
        args.append(dt)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # Get total count
    total_sql = f"SELECT COUNT(*) AS c FROM transactions t {where_clause}"
    total_res = query_one(total_sql, tuple(args))
    total = total_res["c"] if total_res else 0

    # Get Paginated Results
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
    
    # Execute query with limit/offset added to args
    rows = query(sql, tuple(args + [per_page, offset]))

    def serialize(r):
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, "isoformat"): 
                d[k] = str(v)[:16] # Format date
            elif hasattr(v, "__float__"): 
                d[k] = float(v)    # Format Decimal/Float
        return d

    return jsonify({
        "total": total,
        "page": page,
        "pages": max((total + per_page - 1) // per_page, 1),
        "rows": [serialize(r) for r in rows]
    })