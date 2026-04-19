"""modules/receipt.py"""
from flask import Blueprint, abort, jsonify, render_template, session
from modules.security import login_required
from modules.db import query_one

receipt_bp = Blueprint("receipt", __name__)

def _get_txn(txn_id, uid, is_admin):
    if is_admin:
        return query_one("SELECT t.*,u.username,u.full_name,u.email,u.mobile FROM transactions t JOIN users u ON t.user_id=u.id WHERE t.id=%s",(txn_id,))
    return query_one("SELECT t.*,u.username,u.full_name,u.email,u.mobile FROM transactions t JOIN users u ON t.user_id=u.id WHERE t.id=%s AND t.user_id=%s",(txn_id,uid))

@receipt_bp.route("/receipt/<int:txn_id>")
@login_required
def receipt(txn_id):
    txn = _get_txn(txn_id, session["user_id"], session.get("role")=="admin")
    if not txn: abort(404)
    return render_template("receipt.html", txn=txn)

@receipt_bp.route("/receipt/<int:txn_id>/json")
@login_required
def receipt_json(txn_id):
    txn = _get_txn(txn_id, session["user_id"], session.get("role")=="admin")
    if not txn: abort(404)
    d = dict(txn)
    for k,v in d.items():
        if hasattr(v,"isoformat"): d[k]=str(v)
        elif hasattr(v,"__float__"): d[k]=float(v)
    return jsonify(d)
