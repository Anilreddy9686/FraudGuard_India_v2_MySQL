"""modules/export.py — CSV + HTML Report"""
import csv, io
from datetime import datetime
from flask import Blueprint, make_response, session
from modules.security import login_required
from modules.db import query, query_one

export_bp = Blueprint("export", __name__)

@export_bp.route("/export/csv")
@login_required
def export_csv():
    uid      = session["user_id"]
    is_admin = session.get("role") == "admin"
    txns     = query("SELECT t.*,u.username FROM transactions t JOIN users u ON t.user_id=u.id ORDER BY t.created_at DESC") if is_admin else query("SELECT * FROM transactions WHERE user_id=%s ORDER BY created_at DESC", (uid,))

    out = io.StringIO()
    w   = csv.writer(out)
    hdr = ["ID","Date","Type","Amount (INR)","Old Bal Sender","New Bal Sender","Old Bal Recv","New Bal Recv","Prediction","Risk","Confidence%"]
    if is_admin: hdr.insert(1,"Username")
    w.writerow(hdr)
    for t in txns:
        row = [t["id"],t["created_at"],t["type"],f"{float(t['amount_inr'] or 0):,.2f}",
               f"{float(t['old_balance_orig'] or 0):,.2f}",f"{float(t['new_balance_orig'] or 0):,.2f}",
               f"{float(t['old_balance_dest'] or 0):,.2f}",f"{float(t['new_balance_dest'] or 0):,.2f}",
               t["prediction"],t["risk_score"],f"{t['confidence']}%"]
        if is_admin: row.insert(1,t["username"])
        w.writerow(row)
    out.seek(0)
    fname = f"ANILREDDY_OPFD_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    resp  = make_response(out.getvalue())
    resp.headers["Content-Disposition"] = f"attachment; filename={fname}"
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    return resp

@export_bp.route("/export/report")
@login_required
def export_report():
    uid      = session["user_id"]
    is_admin = session.get("role") == "admin"
    txns     = query("SELECT t.*,u.username FROM transactions t JOIN users u ON t.user_id=u.id ORDER BY t.created_at DESC LIMIT 100") if is_admin else query("SELECT * FROM transactions WHERE user_id=%s ORDER BY created_at DESC LIMIT 100", (uid,))
    stats    = query_one("SELECT COUNT(*) AS total, SUM(prediction='Fraud') AS frauds, COALESCE(SUM(amount_inr),0) AS volume FROM transactions") if is_admin else query_one("SELECT COUNT(*) AS total, SUM(prediction='Fraud') AS frauds, COALESCE(SUM(amount_inr),0) AS volume FROM transactions WHERE user_id=%s", (uid,))

    total  = int(stats["total"] or 0)
    frauds = int(stats["frauds"] or 0)
    volume = float(stats["volume"] or 0)
    rows   = ""
    for t in txns:
        col  = "#ef4444" if t["prediction"]=="Fraud" else "#22c55e"
        uname = t.get("username", session["username"])
        rows += f"<tr><td>{t['id']}</td><td>{uname}</td><td>{str(t['created_at'])[:16]}</td><td>{t['type']}</td><td>₹{float(t['amount_inr'] or 0):,.2f}</td><td style='color:{col};font-weight:700'>{t['prediction']}</td><td>{t['risk_score']}/100</td></tr>"

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body{{font-family:Arial;margin:30px;color:#111}}h1{{color:#1e3a8a;border-bottom:3px solid #FF9933;padding-bottom:8px}}
.meta{{color:#666;font-size:13px;margin-bottom:20px}}.stats{{display:flex;gap:16px;margin:20px 0;flex-wrap:wrap}}
.stat{{background:#f0f4ff;padding:14px 20px;border-radius:8px;text-align:center;min-width:140px}}
.stat h3{{margin:0 0 4px;font-size:22px;color:#1e3a8a}}.stat p{{margin:0;font-size:12px;color:#555}}
table{{width:100%;border-collapse:collapse;font-size:12px;margin-top:20px}}
th{{background:#1e3a8a;color:#fff;padding:8px 10px;text-align:left}}
td{{padding:7px 10px;border-bottom:1px solid #e5e7eb}}tr:nth-child(even){{background:#f9fafb}}
.footer{{margin-top:24px;font-size:11px;color:#aaa;text-align:center}}
.tricolor{{height:4px;display:flex;margin-bottom:20px}}
.tricolor span{{flex:1}}
</style></head><body>
<div class="tricolor"><span style="background:#FF9933"></span><span style="background:#fff;border:1px solid #ddd"></span><span style="background:#138808"></span></div>
<h1>🛡️ Online Payment Fraud Detection — Report</h1>
<div class="meta">Generated: {datetime.now().strftime('%d %B %Y, %H:%M IST')} | User: <strong>{session['username']}</strong> | Role: <strong>{session.get('role','user').title()}</strong></div>
<div class="stats">
  <div class="stat"><h3>{total}</h3><p>Total Transactions</p></div>
  <div class="stat"><h3 style="color:#ef4444">{frauds}</h3><p>Fraud Detected</p></div>
  <div class="stat"><h3>₹{volume/100000:.1f}L</h3><p>Total Volume</p></div>
  <div class="stat"><h3>{round(frauds/total*100,1) if total else 0}%</h3><p>Fraud Rate</p></div>
</div>
<table><thead><tr><th>ID</th><th>User</th><th>Date</th><th>Type</th><th>Amount</th><th>Result</th><th>Risk</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="footer">Online Payment Fraud Detection &nbsp;•&nbsp; Developed by <strong>ANILREDDY</strong> &nbsp;•&nbsp; 📞 9686809509 &nbsp;•&nbsp; Confidential</div>
</body></html>"""

    fname = f"ANILREDDY_OPFD_Report_{datetime.now().strftime('%Y%m%d')}.html"
    resp  = make_response(html)
    resp.headers["Content-Disposition"] = f"attachment; filename={fname}"
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp
