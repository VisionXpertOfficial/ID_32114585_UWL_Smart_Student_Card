# encode_faces.py
#
# Builds simple perceptual-hash "encodings" for each student portrait.
# These hashes are used by backend/face_match_service.py
#
# Location: frontend/ui/assets/encode_faces.py

from pathlib import Path
from PIL import Image
import imagehash
import json
import pickle

# Root = assets folder
ROOT_DIR = Path(__file__).resolve().parent

STUDENTS_JSON = ROOT_DIR / "students_50.json"
IMAGES_DIR    = ROOT_DIR
ENCODINGS_DIR = ROOT_DIR / "encodings"
ENCODINGS_DIR.mkdir(exist_ok=True)
ENCODINGS_PATH = ENCODINGS_DIR / "face_hashes.pkl"

# ---------------------------------------------------------------------
# Extra “admin” face: Mohammed Suleman Miah (ID 32114585)
# This does NOT change students_50.json on disk. We only extend the
# in-memory list when generating hashes.
# ---------------------------------------------------------------------
EXTRA_STUDENTS = [
    {
        "student_id": "32114585",
        "first_name": "Mohammed",
        # use underscore so filename matches: 32114585_Mohammed_Suleman_Miah.png
        "surname": "Suleman_Miah",
    }
]


def load_students():
    """Load demo students + our extra admin student for hashing."""
    with STUDENTS_JSON.open(encoding="utf-8") as f:
        data = json.load(f)

    # append admin record (only in memory)
    data.extend(EXTRA_STUDENTS)
    return data


def main():
    students = load_students()
    encodings_data = []

    for s in students:
        sid = str(s.get("student_id", "")).strip()
        if not sid:
            continue

        first = str(s.get("first_name", "")).strip().replace(" ", "_")
        surname = str(s.get("surname", "")).strip().replace(" ", "_")

        filename = f"{sid}_{first}_{surname}.png"
        img_path = IMAGES_DIR / filename

        if not img_path.exists():
            print(f"[WARN] Image not found for {sid} at {img_path}")
            continue

        print(f"[INFO] Processing {img_path}")
        with Image.open(img_path) as img:
            h = imagehash.average_hash(img)

        full_name = f"{s.get('first_name','').strip()} {s.get('surname','').strip()}".strip()

        encodings_data.append(
            {
                "student_id": sid,
                "full_name": full_name,
                "filename": filename,
                "hash": str(h),
            }
        )

    with ENCODINGS_PATH.open("wb") as f:
        pickle.dump(encodings_data, f)

    print(f"[OK] Saved {len(encodings_data)} hashes to {ENCODINGS_PATH}")


if __name__ == "__main__":
    main()

# ID_32114585_Mohammed_Miah

