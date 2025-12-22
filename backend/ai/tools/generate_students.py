import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Output paths
CSV_OUTPUT = Path("ai/data/students_50.csv")
JSON_OUTPUT = Path("ui/assets/students_50.json")

COURSES = [
    "Computer Science",
    "Cyber Security",
    "Business Computing",
    "Data Science",
    "Software Engineering",
]

FIRST_NAMES = [
    "Mohammed", "Zaynab", "Ismaeel", "Aisha", "James",
    "Amir", "Sofia", "Sarah", "Daniel", "Emily",
    "Hassan", "Yusuf", "Fatima", "Adam"
]

LAST_NAMES = [
    "Miah", "Khan", "Patel", "Smith", "Brown",
    "Ali", "Hussain", "Begum", "Ahmed", "Taylor"
]


def random_date(start, end):
    delta = end - start
    offset = random.randint(0, delta.days)
    return start + timedelta(days=offset)


def generate_label(consent, dist_km, fail_cnt, device_change):
    risk = dist_km + fail_cnt * 5 + device_change * 3

    if not consent:
        return "manual_review"
    if risk <= 12:
        return "approved"
    if risk >= 30:
        return "rejected"
    return "manual_review"


def main(n_students=50):
    start_valid = datetime(2025, 9, 1)
    end_valid = datetime(2026, 1, 31)

    rows = []

    for i in range(1, n_students + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        course = random.choice(COURSES)

        student_id = f"ID_32{i:06d}_{first}_{last}"

        valid_from = random_date(start_valid, end_valid)
        valid_to = valid_from + timedelta(days=365)

        hour = random.randint(0, 23)
        dist_km = random.randint(0, 30)
        fail_cnt = random.randint(0, 5)
        device_change = random.randint(0, 3)
        consent = random.choice([True, True, True, False])

        label = generate_label(consent, dist_km, fail_cnt, device_change)

        row = {
            "student_id": student_id,
            "first_name": first,
            "surname": last,
            "course": course,
            "valid_from": valid_from.strftime("%Y-%m-%d"),
            "valid_to": valid_to.strftime("%Y-%m-%d"),
            "hour": hour,
            "dist_km": dist_km,
            "fail_cnt": fail_cnt,
            "device_change": device_change,
            "consent": str(consent).lower(),
            "label": label
        }

        rows.append(row)

    # --- Write CSV ---
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # --- Write JSON ---
    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with JSON_OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print("[OK] Generated CSV and JSON successfully.")


if __name__ == "__main__":
    main()
