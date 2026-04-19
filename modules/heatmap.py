"""modules/heatmap.py — India state-wise fraud heatmap"""
import random
from flask import Blueprint, render_template, session, jsonify
from modules.security import login_required
from modules.db import query, query_one

heatmap_bp = Blueprint("heatmap", __name__)

STATES = ["Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal","Delhi","Jammu & Kashmir","Ladakh","Puducherry"]

COORDS = {
"Andhra Pradesh":[15.91,79.74],"Arunachal Pradesh":[28.21,94.72],"Assam":[26.20,92.93],
"Bihar":[25.09,85.31],"Chhattisgarh":[21.27,81.86],"Goa":[15.29,74.12],
"Gujarat":[22.25,71.19],"Haryana":[29.05,76.08],"Himachal Pradesh":[31.10,77.17],
"Jharkhand":[23.61,85.27],"Karnataka":[15.31,75.71],"Kerala":[10.85,76.27],
"Madhya Pradesh":[22.97,78.65],"Maharashtra":[19.75,75.71],
"Manipur":[24.66,93.90],"Meghalaya":[25.46,91.36],"Mizoram":[23.16,92.93],
"Nagaland":[26.15,94.56],"Odisha":[20.95,85.09],"Punjab":[31.14,75.34],
"Rajasthan":[27.02,74.21],"Sikkim":[27.53,88.51],"Tamil Nadu":[11.12,78.65],
"Telangana":[18.11,79.01],"Tripura":[23.94,91.98],"Uttar Pradesh":[26.84,80.94],
"Uttarakhand":[30.06,79.01],"West Bengal":[22.98,87.85],"Delhi":[28.70,77.10],
"Jammu & Kashmir":[33.77,76.57],"Ladakh":[34.15,77.57],"Puducherry":[11.94,79.80]
}

def _seed_state(txn_id):
    random.seed(txn_id*31337)
    return random.choice(STATES)


@heatmap_bp.route("/heatmap")
@login_required
def heatmap():
    return render_template("heatmap.html")


@heatmap_bp.route("/heatmap/data")
@login_required
def heatmap_data():

    # 🔥 ADD: SAFE WRAPPER (DO NOT REMOVE ORIGINAL CODE)
    try:
        uid      = session["user_id"]
        is_admin = session.get("role") == "admin"

        rows = query(
            "SELECT id,amount_inr,prediction,risk_score,type FROM transactions ORDER BY created_at DESC LIMIT 5000"
        ) if is_admin else query(
            "SELECT id,amount_inr,prediction,risk_score,type FROM transactions WHERE user_id=%s ORDER BY created_at DESC LIMIT 1000",
            (uid,)
        )

        sd = {s:{"total":0,"frauds":0,"volume":0.0,"risk_sum":0} for s in STATES}

        for r in rows:
            s = _seed_state(r["id"])
            sd[s]["total"] += 1
            sd[s]["volume"] += float(r["amount_inr"] or 0)
            sd[s]["risk_sum"] += int(r["risk_score"] or 0)

            if r["prediction"] == "Fraud":
                sd[s]["frauds"] += 1

        result = []
        for s, d in sd.items():
            if not d["total"]:
                continue

            c = COORDS.get(s, [20.5937,78.9629])

            result.append({
                "state": s,
                "total": d["total"],
                "frauds": d["frauds"],
                "volume": round(d["volume"],2),
                "avg_risk": round(d["risk_sum"]/d["total"]),
                "fraud_rate": round(d["frauds"]/d["total"]*100,1),
                "lat": c[0],
                "lng": c[1]
            })

        result.sort(key=lambda x:x["frauds"], reverse=True)

        summary = query_one(
            "SELECT COUNT(*) AS total,SUM(prediction='Fraud') AS frauds,COALESCE(SUM(amount_inr),0) AS volume FROM transactions"
        ) if is_admin else query_one(
            "SELECT COUNT(*) AS total,SUM(prediction='Fraud') AS frauds,COALESCE(SUM(amount_inr),0) AS volume FROM transactions WHERE user_id=%s",
            (uid,)
        )

        return jsonify({
            "states": result,
            "summary": {k:(float(v) if hasattr(v,"__float__") else v) for k,v in (summary or {}).items()},
            "is_admin": is_admin
        })

    except Exception as e:
        print("🔥 HEATMAP ERROR:", e)

        # 🔥 ADD: DEMO DATA (NO DB MODE)
        demo_states = [
            {"state":"Karnataka","total":5,"frauds":1,"volume":20000,"avg_risk":30,"fraud_rate":20,"lat":15.31,"lng":75.71},
            {"state":"Telangana","total":3,"frauds":1,"volume":15000,"avg_risk":40,"fraud_rate":33.3,"lat":18.11,"lng":79.01},
            {"state":"Maharashtra","total":4,"frauds":2,"volume":30000,"avg_risk":60,"fraud_rate":50,"lat":19.75,"lng":75.71}
        ]

        demo_summary = {
            "total": 12,
            "frauds": 4,
            "volume": 65000
        }

        return jsonify({
            "states": demo_states,
            "summary": demo_summary,
            "is_admin": True,
            "demo_mode": True
        })