"""modules/predict.py — Dashboard + Fraud Prediction + INR"""
import os, pickle
import numpy as np
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from modules.security import login_required, validate_transaction_input, audit
from modules.db import execute, query, query_one

predict_bp = Blueprint("predict", __name__)

# Load ML model
model = None
for _p in [
    os.path.join(os.path.dirname(__file__), "..", "payments.pkl"),
    os.path.join(os.path.dirname(__file__), "..", "..", "payments.pkl"),
]:
    try:
        model = pickle.load(open(_p, "rb"))
        print(f"✅ ML model loaded: {_p}")
        break
    except Exception:
        pass
if not model:
    print("⚠️  ML model not found — rule-based fallback active")

TXN_TYPES = {1:"CASH_IN", 2:"CASH_OUT", 3:"DEBIT", 4:"PAYMENT", 5:"TRANSFER"}

_INDIA_RULES = [
    {"fn": lambda t,a: t in (4,5) and a > 2_000_000, "risk": 80},
    {"fn": lambda t,a: a % 100_000 == 0 and a >= 100_000, "risk": 55},
    {"fn": lambda t,a: t == 2 and a > 500_000, "risk": 70},
    {"fn": lambda t,a: t == 5 and 99_999 < a < 200_001, "risk": 40},
    {"fn": lambda t,a: t == 3 and a > 1_000_000, "risk": 65},
]


def fmt_inr(amount):
    try:
        v = float(amount or 0)
        if v >= 10_000_000: return f"₹{v/10_000_000:.2f} Cr"
        if v >= 100_000:    return f"₹{v/100_000:.2f} L"
        if v >= 1_000:      return f"₹{v/1_000:.2f} K"
        return f"₹{v:,.2f}"
    except Exception:
        return f"₹{amount}"


def _risk_score(t_type, amount, old_orig, new_orig):
    score = 0
    for rule in _INDIA_RULES:
        try:
            if rule["fn"](t_type, amount): score += rule["risk"]
        except Exception: pass
    if abs((old_orig - new_orig) - amount) > 1_000: score += 20
    if new_orig == 0 and old_orig > 0:               score += 30
    return min(score, 100)


@predict_bp.route("/dashboard")
@login_required
def dashboard():
    uid   = session["user_id"]
    stats = query_one("""
        SELECT COUNT(*) AS total, SUM(prediction='Fraud') AS frauds,
               SUM(prediction='Legitimate') AS legit,
               COALESCE(SUM(amount_inr),0) AS total_amount
        FROM transactions WHERE user_id=%s
    """, (uid,))
    recent = query("""
        SELECT * FROM transactions WHERE user_id=%s
        ORDER BY created_at DESC LIMIT 6
    """, (uid,))
    unread = query_one(
        "SELECT COUNT(*) AS c FROM alerts WHERE user_id=%s AND is_read=0", (uid,)
    )["c"]
    return render_template("dashboard.html",
                           stats=stats, recent=recent,
                           alerts_count=unread, fmt_inr=fmt_inr)


@predict_bp.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    if request.method == "POST":
        # Server-side validation (never trust frontend)
        errors = validate_transaction_input(request.form)
        if errors:
            for e in errors: flash(e, "danger")
            return redirect(url_for("predict.predict"))

        try:
            step     = int(request.form["step"])
            t_type   = int(request.form["type"])
            amount   = float(request.form["amount"])
            old_orig = float(request.form["oldbalanceOrg"])
            new_orig = float(request.form["newbalanceOrig"])
            old_dest = float(request.form["oldbalanceDest"])
            new_dest = float(request.form["newbalanceDest"])
        except (KeyError, ValueError) as exc:
            flash("Invalid input detected.", "danger")
            return redirect(url_for("predict.predict"))

        risk     = _risk_score(t_type, amount, old_orig, new_orig)
        features = np.array([[step, t_type, amount, old_orig, new_orig, old_dest, new_dest]])

        if model:
            pred_raw   = model.predict(features)[0]
            try:
                prob       = model.predict_proba(features)[0]
                confidence = round(float(max(prob)) * 100, 1)
            except Exception:
                confidence = 85.0
            result = "Fraud" if pred_raw == 1 else "Legitimate"
        else:
            result     = "Fraud" if risk > 60 else "Legitimate"
            confidence = float(risk) if risk > 60 else float(100 - risk)

        if result == "Fraud":
            risk = max(risk, 65)

        txn_id = execute("""
            INSERT INTO transactions
              (user_id,step,type,amount_inr,old_balance_orig,new_balance_orig,
               old_balance_dest,new_balance_dest,prediction,confidence,risk_score,ip_address)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (session["user_id"], step, TXN_TYPES.get(t_type,str(t_type)),
              amount, old_orig, new_orig, old_dest, new_dest,
              result, confidence, risk, request.remote_addr))

        if result == "Fraud" or risk > 70:
            execute("""
                INSERT INTO alerts (user_id,transaction_id,alert_type,message)
                VALUES (%s,%s,%s,%s)
            """, (session["user_id"], txn_id, "FRAUD_ALERT",
                  f"⚠️ High-risk transaction: {fmt_inr(amount)} via "
                  f"{TXN_TYPES.get(t_type,'?')} — Risk: {risk}/100"))

        audit(session["user_id"], "PREDICT",
              f"Txn #{txn_id} = {result} (risk {risk})")

        return render_template("result.html",
                               result=result, confidence=confidence,
                               risk=risk, amount=fmt_inr(amount),
                               txn_type=TXN_TYPES.get(t_type, str(t_type)),
                               txn_id=txn_id)

    return render_template("predict.html", txn_types=TXN_TYPES)
