# backend/api.py

from flask import Flask, jsonify, request
from pathlib import Path
import csv

import face_match_service  # <-- our helper module that does the hashing/matching

app = Flask(__name__)

# ----------------------------------------------------------------------
# CORS – allow calls from your frontend (Live Server / browser)
# ----------------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    # If you want to lock it to Live Server only, replace "*" with
    # "http://127.0.0.1:5500" (or whatever port Live Server uses).
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


# --- Paths & data loading -------------------------------------------------

# Path to this file: backend/api.py
BASE_DIR = Path(__file__).resolve().parent

# CSV with student data: backend/ai/data/students_50.csv
STUDENTS_CSV_PATH = BASE_DIR / "ai" / "data" / "students_50.csv"


def load_students():
    """Load all students into memory as a list of dicts."""
    students = []
    try:
        with STUDENTS_CSV_PATH.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                students.append(row)
    except FileNotFoundError:
        print(f"[ERROR] Could not find students CSV at: {STUDENTS_CSV_PATH}")
    return students


STUDENTS = load_students()
print(f"[INFO] Loaded {len(STUDENTS)} students from CSV")


# --- Basic health check ---------------------------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running"})


# --- API: get all students ------------------------------------------------

@app.route("/students", methods=["GET"])
def get_all_students():
    """Return the full list of students."""
    return jsonify(STUDENTS)


# --- API: get a single student by ID -------------------------------------

@app.route("/students/<student_id>", methods=["GET"])
def get_student_by_id(student_id):
    """
    Return one student whose student_id matches the URL path.
    Example: /students/32000001
    """
    student = next(
        (s for s in STUDENTS if s.get("student_id") == student_id),
        None,
    )

    if student is None:
        return jsonify({"error": "Student not found", "student_id": student_id}), 404

    return jsonify(student)


# --- API: AI face match by filename --------------------------------------

@app.route("/face-match", methods=["POST", "OPTIONS"])
def face_match():
    """
    Match an image (by filename) against the stored student portraits.

    Expects JSON body:
        { "filename": "32000025_Aisha_Taylor.png" }

    Returns (example):
        {
          "student_id": "32000025",
          "distance": 0,
          "student": { ...full student row from students_50.csv... }
        }
    """

    # Handle CORS preflight
    if request.method == "OPTIONS":
        # Empty 204 response; headers are added by add_cors_headers()
        return ("", 204)

    data = request.get_json(silent=True) or {}
    filename = data.get("filename")

    if not filename:
        return jsonify({"error": "filename is required"}), 400

    try:
        result = face_match_service.match_by_filename(filename)
    except FileNotFoundError:
        return jsonify({"error": f"Image not found: {filename}"}), 404

    if result is None:
        return jsonify({"error": "No students in database"}), 500

    return jsonify(result)


if __name__ == "__main__":
    # For development only
    app.run(host="127.0.0.1", port=5000, debug=True)

# ID_32114585_Mohammed_Miah




