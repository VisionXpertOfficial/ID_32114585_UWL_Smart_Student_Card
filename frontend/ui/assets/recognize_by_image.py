# recognize_by_image.py
# Ask for an image filename, compare it to all stored hashes,
# and print the best-matching student.

import os
import json
import pickle
from PIL import Image
import imagehash
import numpy as np  # <-- needed to handle list-of-bool hashes

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENTS_JSON = os.path.join(ROOT_DIR, "students_50.json")
ENCODINGS_PATH = os.path.join(ROOT_DIR, "encodings", "face_hashes.pkl")

# Load students
with open(STUDENTS_JSON, "r", encoding="utf-8") as f:
    students = json.load(f)
students_by_id = {str(s["student_id"]): s for s in students}

# Load stored hashes
with open(ENCODINGS_PATH, "rb") as f:
    encodings_data = pickle.load(f)


def record_to_hash(rec):
    """
    Convert whatever is stored in rec["hash"] into an ImageHash object.
    It supports:
      - hex string (e.g. 'ffe012...')
      - list/array of booleans (old format)
    """
    v = rec["hash"]

    # Case 1: hex string (newer format)
    if isinstance(v, str):
        return imagehash.hex_to_hash(v)

    # Case 2: list/array of booleans (older format)
    arr = np.array(v, dtype=bool)
    return imagehash.ImageHash(arr)


def main():
    print("Example: 32000005_Aisha_Miah.png")
    fname = input("Type image filename to recognise (must be in this folder): ").strip()

    img_path = os.path.join(ROOT_DIR, fname)
    if not os.path.exists(img_path):
        print(f"[ERROR] File not found: {img_path}")
        return

    img = Image.open(img_path).convert("RGB")
    target_hash = imagehash.average_hash(img)

    best_id = None
    best_dist = None

    for rec in encodings_data:
        h = record_to_hash(rec)
        dist = target_hash - h  # Hamming distance between hashes
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_id = str(rec["student_id"])

    if best_id is None:
        print("[RESULT] No students in database.")
        return

    student = students_by_id.get(best_id, {})
    full_name = f"{student.get('first_name', '')} {student.get('surname', '')}".strip()
    print("====================================")
    print(f"[MATCH] Student ID: {best_id}")
    print(f"        Name      : {full_name}")
    print(f"        Distance  : {best_dist}")
    print("====================================")


if __name__ == "__main__":
    main()

# ID_32114585_Mohammed_Miah
