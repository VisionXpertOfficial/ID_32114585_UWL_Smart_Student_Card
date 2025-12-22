from flask import Flask, request, jsonify
from math import exp

app = Flask(__name__)

# -------------------------------
# Simple sigmoid scoring function
# -------------------------------
def sigmoid(x):
    return 1 / (1 + exp(-x))


# ----------------------------------------
# AI Verification Endpoint  (POST /verify)
# ----------------------------------------
@app.route("/verify", methods=["POST"])
def verify():
    data = request.get_json(force=True) or {}

    # Extract features from UI
    hour          = float(data.get("hour", 12))
    dist_km       = float(data.get("dist_km", 0))
    fail_cnt      = float(data.get("fail_cnt", 0))
    device_change = float(data.get("device_change", 0))

    # -------------------------------------------------
    # Basic "AI" anomaly scoring for demo purposes:
    # -------------------------------------------------
    z = (
        (dist_km / 30.0) * 2.2 +
        (fail_cnt / 5.0) * 2.5 +
        (1.5 if device_change else 0.0) +
        (1.0 if hour < 7 or hour > 22 else 0.0)
    )

    score = round(float(sigmoid(z)), 3)  # Output between 0 and 1

    anomaly = score > 0.7  # Flag if score > 70%

    return jsonify({
        "ok": True,
        "anomaly": anomaly,
        "score": score
    })


# -------------------------------
# RUN SERVER (port 5051)
# -------------------------------
if __name__ == "__main__":
    print("AI API running at http://127.0.0.1:5051")
    app.run(host="0.0.0.0", port=5051, debug=True)
