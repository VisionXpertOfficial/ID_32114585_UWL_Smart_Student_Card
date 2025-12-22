"""
Simple unit-style tests for the AI verification API.
Run this while ai_api.py is running on http://127.0.0.1:5051
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5051"


def call_verify(case_name, hour, dist_km, fail_cnt, device_change):
    payload = {
        "hour": hour,
        "dist_km": dist_km,
        "fail_cnt": fail_cnt,
        "device_change": device_change,
    }

    print(f"\n=== Test case: {case_name} ===")
    print("Request:", json.dumps(payload))

    try:
        resp = requests.post(f"{BASE_URL}/verify", json=payload, timeout=5)
    except Exception as e:
        print("ERROR: could not reach AI API:", e)
        return

    print("HTTP status:", resp.status_code)

    try:
        data = resp.json()
    except Exception:
        print("Response was not JSON:", resp.text)
        return

    print("Response JSON:", json.dumps(data, indent=2))

    # --- Simple pass/fail rule for logging (you can describe this in report) ---
    decision = data.get("decision", "").lower()
    score = data.get("score", None)

    if decision in {"approve", "approved", "low-risk", "low_risk"}:
        outcome = "PASS (expected low risk)"
    elif decision in {"review", "manual_review"}:
        outcome = "CHECK MANUALLY (borderline case)"
    elif decision in {"block", "denied", "high-risk", "high_risk"}:
        outcome = "PASS (expected high risk / blocked)"
    else:
        outcome = "UNKNOWN decision, check logic"

    print(f"Outcome: {outcome}")
    if score is not None:
        print(f"Model score: {score:.4f}")


def main():
    # You can tweak these test cases to match what your model does
    call_verify("Normal morning login", hour=9, dist_km=3, fail_cnt=0, device_change=0)
    call_verify("Late night suspicious login", hour=23, dist_km=40, fail_cnt=2, device_change=1)
    call_verify("New device far away + many fails", hour=2, dist_km=500, fail_cnt=5, device_change=1)


if __name__ == "__main__":
    main()
