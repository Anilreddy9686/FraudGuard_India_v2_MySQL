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

    conditions = [] if is_admin else [f"t.user_id={uid}"]
    if filt == "fraud":  conditions.append("t.prediction='Fraud'")
    if filt == "legit":  conditions.append("t.prediction='Legitimate'")
    w = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    total = query_one(f"SELECT COUNT(*) AS c FROM transactions t {w}")["c"]
    if is_admin:
        rows = query(f"SELECT t.*,u.username FROM transactions t JOIN users u ON t.user_id=u.id {w} ORDER BY t.created_at DESC LIMIT %s OFFSET %s", (per_page, offset))
    else:
        rows = query(f"SELECT * FROM transactions t {w} ORDER BY t.created_at DESC LIMIT %s OFFSET %s", (per_page, offset))

    pages = max((total + per_page - 1) // per_page, 1)
    return render_template("history.html", txns=rows, page=page, pages=pages,
                           total=total, filt=filt, is_admin=is_admin)
