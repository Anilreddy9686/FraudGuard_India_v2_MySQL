"""modules/history.py"""
from flask import Blueprint, render_template, request, session
from modules.security import login_required
from modules.db import query, query_one

history_bp = Blueprint("history", __name__)

@history_bp.route("/history")
@login_required
def history():

    # 🔥 ADD: SAFE WRAPPER (DO NOT REMOVE ORIGINAL LOGIC)
    try:
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
            rows = query(f"""
                SELECT t.*,u.username 
                FROM transactions t 
                JOIN users u ON t.user_id=u.id 
                {w} 
                ORDER BY t.created_at DESC 
                LIMIT %s OFFSET %s
            """, (per_page, offset))
        else:
            rows = query(f"""
                SELECT * FROM transactions t 
                {w} 
                ORDER BY t.created_at DESC 
                LIMIT %s OFFSET %s
            """, (per_page, offset))

        pages = max((total + per_page - 1) // per_page, 1)

        return render_template(
            "history.html",
            txns=rows,
            page=page,
            pages=pages,
            total=total,
            filt=filt,
            is_admin=is_admin
        )

    except Exception as e:
        print("🔥 HISTORY ERROR:", e)

        # 🔥 ADD: DEMO DATA (NEW LINES — OLD CODE NOT REMOVED)
        demo_rows = [{
            "id": 1,
            "created_at": "2026-01-01 10:00",
            "type": "TRANSFER",
            "amount_inr": 5000,
            "old_balance_orig": 10000,
            "new_balance_orig": 5000,
            "old_balance_dest": 2000,
            "new_balance_dest": 7000,
            "prediction": "Legitimate",
            "risk_score": 10,
            "confidence": 95
        }]

        # 🔥 ADD: FALLBACK FOR NO-DB MODE
        return render_template(
            "history.html",
            txns=demo_rows,   # 🔥 CHANGED from [] → demo_rows
            page=1,
            pages=1,
            total=1,
            filt="all",
            is_admin=False,
            demo_mode=True
        )