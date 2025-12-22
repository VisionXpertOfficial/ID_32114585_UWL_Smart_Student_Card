"""
face_match_service.py
Shared helper used by the backend to match a face image
against the 30 student portraits and return the best match.

It reuses the hashes you generated in:
frontend/ui/assets/encodings/face_hashes.pkl
"""

from pathlib import Path
import json
import pickle

from PIL import Image
import imagehash
import numpy as np


# This file lives in: .../ID_32114585_Mohammed_Miah_UWL_Smart_Card/backend
# So ROOT_DIR is the project root folder.
ROOT_DIR = Path(__file__).resolve().parents[1]

ASSETS_DIR = ROOT_DIR / "frontend" / "ui" / "assets"
STUDENTS_JSON = ASSETS_DIR / "students_50.json"
ENCODINGS_PATH = ASSETS_DIR / "encodings" / "face_hashes.pkl"

# --- Load students -----------------------------------------------------------

with STUDENTS_JSON.open("r", encoding="utf-8") as f:
    STUDENTS = json.load(f)

STUDENTS_BY_ID = {str(s["student_id"]): s for s in STUDENTS}

# --- Load stored image hashes ------------------------------------------------

with ENCODINGS_PATH.open("rb") as f:
    ENCODINGS_DATA = pickle.load(f)


def _record_to_hash(rec):
    """
    Convert whatever is in rec["hash"] into an imagehash.ImageHash.

    Supports:
      - hex string (e.g. 'ffe012...')
      - list/array of booleans (older format)
    """
    v = rec["hash"]

    # Case 1: hex string
    if isinstance(v, str):
        return imagehash.hex_to_hash(v)

    # Case 2: list/array of booleans
    arr = np.array(v, dtype=bool)
    return imagehash.ImageHash(arr)


def match_by_filename(filename: str):
    """
    Given an image filename like '32000025_Aisha_Taylor.png'
    (stored in frontend/ui/assets), find the best-matching student.

    Returns a dict with:
        {
          "student_id": "32000025",
          "distance": 0,
          "student": { ... full student record ... }
        }
    or None if no students are available.
    """
    img_path = ASSETS_DIR / filename

    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {img_path}")

    img = Image.open(img_path).convert("RGB")
    target_hash = imagehash.average_hash(img)

    best_id = None
    best_dist = None

    for rec in ENCODINGS_DATA:
        h = _record_to_hash(rec)
        dist = target_hash - h  # Hamming distance

        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_id = str(rec["student_id"])

    if best_id is None:
        return None

    student = STUDENTS_BY_ID.get(best_id, {})
    return {
        "student_id": best_id,
        "distance": int(best_dist),
        "student": student,
    }


# Small self-test when run directly from the terminal
if __name__ == "__main__":
    test_file = "32000025_Aisha_Taylor.png"  # change if you like
    result = match_by_filename(test_file)
    print("Test file:", test_file)
    print("Result:  ", result)

# ID_32114585_Mohammed_Miah
