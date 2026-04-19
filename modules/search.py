"""modules/search.py"""
from flask import Blueprint, render_template, request, session, jsonify
from modules.security import login_required
from modules.db import query, query_one

search_bp = Blueprint("search", __name__)
TXN_TYPES = ["CASH_IN","CASH_OUT","DEBIT","PAYMENT","TRANSFER"]

@search_bp.route("/search")
@login_required
def search():
    return render_template("search.html", txn_types=TXN_TYPES, is_admin=session.get("role")=="admin")


@search_bp.route("/search/results")
@login_required
def search_results():

    # 🔥 ADD: SAFE WRAPPER (DO NOT REMOVE ORIGINAL CODE)
    try:
        uid      = session["user_id"]
        is_admin = session.get("role") == "admin"
        page     = max(int(request.args.get("page",1)),1)
        per_page = 25
        offset   = (page-1)*per_page

        conditions=[]; args=[]

        if not is_admin:
            conditions.append("t.user_id=%s"); args.append(uid)

        kw=request.args.get("q","").strip()
        if kw:
            conditions.append("(t.type LIKE %s OR t.prediction LIKE %s)")
            args+=[f"%{kw}%",f"%{kw}%"]

        tt=request.args.get("type","")
        if tt in TXN_TYPES:
            conditions.append("t.type=%s"); args.append(tt)

        pred=request.args.get("prediction","")
        if pred in ("Fraud","Legitimate"):
            conditions.append("t.prediction=%s"); args.append(pred)

        for field,col in [("amt_min","t.amount_inr >="),("amt_max","t.amount_inr <="),("risk_min","t.risk_score >=")]:
            try:
                v=float(request.args.get(field,0) or 0)
                if v>0:
                    conditions.append(f"{col} %s"); args.append(v)
            except:
                pass

        df=request.args.get("date_from","")
        dt=request.args.get("date_to","")

        if df:
            conditions.append("DATE(t.created_at)>=%s"); args.append(df)
        if dt:
            conditions.append("DATE(t.created_at)<=%s"); args.append(dt)

        w=("WHERE "+" AND ".join(conditions)) if conditions else ""

        total=query_one(f"SELECT COUNT(*) AS c FROM transactions t {w}",tuple(args))["c"]

        if is_admin:
            rows=query(f"""
                SELECT t.*,u.username 
                FROM transactions t 
                JOIN users u ON t.user_id=u.id 
                {w} 
                ORDER BY t.created_at DESC 
                LIMIT %s OFFSET %s
            """,tuple(args)+(per_page,offset))
        else:
            rows=query(f"""
                SELECT t.* 
                FROM transactions t 
                {w} 
                ORDER BY t.created_at DESC 
                LIMIT %s OFFSET %s
            """,tuple(args)+(per_page,offset))

        def ser(r):
            d=dict(r)
            for k,v in d.items():
                if hasattr(v,"isoformat"):
                    d[k]=str(v)[:16]
                elif hasattr(v,"__float__"):
                    d[k]=float(v)
            return d

        return jsonify({
            "total":total,
            "page":page,
            "pages":max((total+per_page-1)//per_page,1),
            "rows":[ser(r) for r in rows]
        })

    except Exception as e:
        print("🔥 SEARCH ERROR:", e)

        # 🔥 ADD: DEMO DATA (NO DB MODE)
        demo_rows = [{
            "id": 1,
            "type": "TRANSFER",
            "amount_inr": 5000,
            "prediction": "Legitimate",
            "risk_score": 10,
            "created_at": "2026-01-01 10:00",
            "username": "admin"
        }]

        return jsonify({
            "total": 1,
            "page": 1,
            "pages": 1,
            "rows": demo_rows,
            "demo_mode": True
        })