// ui/student_loader.js
// Load students, search by ID or name, fill the form + card,
// and call the backend /face-match so AI loops through all faces
// and tells us if the photo matches the selected student.

// === Config ===
const STUDENTS_DATA_URL = "assets/students_50.json";      // JSON with 50 students
const FACE_API_URL      = "http://127.0.0.1:5000/face-match"; // Flask face-match endpoint

// In-memory data
let STUDENTS_LIST = [];
let STUDENTS_BY_ID = {};

// ---- Small helpers ------------------------------------------------------

function uiLog(msg) {
  const box = document.getElementById("logs");
  if (!box) return;
  const ts = new Date().toTimeString().slice(0, 8);
  box.value += `[${ts}] ${msg}\n`;
  box.scrollTop = box.scrollHeight;
}

// Safe toast: uses app.js showToast if available, else alert
function notifyToast(message) {
  if (typeof window.showToast === "function") {
    window.showToast(message);
  } else {
    alert(message);
  }
}

// ---- 1. Load all students from JSON -------------------------------------

async function loadStudentsDataset() {
  try {
    const res = await fetch(STUDENTS_DATA_URL);
    const data = await res.json();

    STUDENTS_LIST = Array.isArray(data) ? data : [];
    STUDENTS_BY_ID = {};

    STUDENTS_LIST.forEach(s => {
      if (s.student_id) {
        STUDENTS_BY_ID[String(s.student_id)] = s;
      }
    });

    console.log("[OK] Loaded", STUDENTS_LIST.length, "students");
    uiLog(`[init] Loaded ${STUDENTS_LIST.length} students from JSON.`);
  } catch (err) {
    console.error("Failed to load student dataset:", err);
    uiLog(`[ERROR] Failed to load students_50.json: ${err.message || err}`);
  }
}

// ---- 2. Find student by ID OR name --------------------------------------

function findStudentByInput(raw) {
  if (!raw) return null;

  const input = raw.trim();
  if (!input) return null;

  const lower = input.toLowerCase();

  // Case 1: only digits → treat as student_id
  if (/^\d+$/.test(input)) {
    return STUDENTS_BY_ID[input] || null;
  }

  // Name search (allow spaces/underscores)
  const normName = lower.replace(/_/g, " ").replace(/\s+/g, " ").trim();

  // Prefer exact "first_name surname"
  let match = STUDENTS_LIST.find(s =>
    `${(s.first_name || "").toLowerCase()} ${(s.surname || "").toLowerCase()}`
      .trim() === normName
  );
  if (match) return match;

  // Fallback: match by first name OR surname only
  match = STUDENTS_LIST.find(s =>
    (s.first_name || "").toLowerCase() === normName ||
    (s.surname || "").toLowerCase() === normName
  );

  return match || null;
}

// ---- 3. Fill the left-side form -----------------------------------------

function fillFormFromStudent(s) {
  const idInput    = document.getElementById("studentIdInput");
  const firstName  = document.getElementById("first_name");
  const surname    = document.getElementById("surname");
  const course     = document.getElementById("course");
  const validFrom  = document.getElementById("valid_from");
  const validTo    = document.getElementById("valid_to");
  const hourEl     = document.getElementById("hour");
  const distEl     = document.getElementById("dist_km");
  const failEl     = document.getElementById("fail_cnt");
  const deviceEl   = document.getElementById("device_change");

  if (idInput)   idInput.value   = s.student_id || "";
  if (firstName) firstName.value = s.first_name || "";
  if (surname)   surname.value   = s.surname || "";
  if (course)    course.value    = s.course || "";

  if (validFrom) validFrom.value = s.valid_from || "";
  if (validTo)   validTo.value   = s.valid_to || "";

  if (hourEl)   hourEl.value   = s.hour ?? "";
  if (distEl)   distEl.value   = s.dist_km ?? "";
  if (failEl)   failEl.value   = s.fail_cnt ?? "";
  if (deviceEl) deviceEl.value = s.device_change ?? "";
}

// ---- 4. Update the right-hand card preview -------------------------------

function updateCardPreview(s) {
  const fullName = `${s.first_name || ""} ${s.surname || ""}`.trim();

  const cardName   = document.getElementById("card_name");
  const cardId     = document.getElementById("card_id");
  const cardCourse = document.getElementById("card_course");
  const cardValid  = document.getElementById("card_valid");
  const photoEl    = document.querySelector(".card .photo");

  if (cardName)   cardName.textContent   = fullName || "Student Name";
  if (cardId)     cardId.textContent     = s.student_id || "";
  if (cardCourse) cardCourse.textContent = s.course || "";
  if (cardValid && s.valid_from && s.valid_to) {
    cardValid.textContent = `${s.valid_from} — ${s.valid_to}`;
  }

  if (photoEl && s.student_id && s.first_name && s.surname) {
    const fileName = `${s.student_id}_${s.first_name}_${s.surname}`
      .replace(/\s+/g, "_") + ".png";
    photoEl.src = `assets/${fileName}`;
    photoEl.alt = `Photo of ${fullName || "student"}`;
  }
}

// ---- 5. Ask backend AI to face-match this student's photo ----------------

async function runFaceMatchForStudent(s) {
  if (!s.student_id || !s.first_name || !s.surname) {
    uiLog("face-match: missing student_id/first_name/surname; skipping.");
    return;
  }

  const filename = `${s.student_id}_${s.first_name}_${s.surname}`
    .replace(/\s+/g, "_") + ".png";

  const payload = { filename };
  uiLog(`face-match: POST ${FACE_API_URL} ${JSON.stringify(payload)}`);

  try {
    const resp = await fetch(FACE_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    let data = null;
    try { data = await resp.json(); } catch { /* ignore parse error */ }

    if (!resp.ok) {
      uiLog(`face-match ERROR ${resp.status}: ${JSON.stringify(data)}`);
      notifyToast("Face-match service error.");
      return;
    }

    if (!data || !data.student) {
      uiLog("face-match: unexpected response format.");
      notifyToast("No face-match result returned.");
      return;
    }

    const matched = data.student;
    const matchedId = String(matched.student_id || matched.id || "");
    const currentId = String(s.student_id || "");
    const distance  = typeof data.distance !== "undefined"
      ? Number(data.distance)
      : NaN;

    // You can adjust this threshold if needed
    const THRESHOLD = 5; // smaller distance = more similar (for imagehash)

    if (matchedId === currentId && (isNaN(distance) || distance <= THRESHOLD)) {
      uiLog(
        `face-match OK: image matches student ${matchedId} ` +
        `(${matched.first_name} ${matched.surname}), distance=${distance}`
      );
      notifyToast("✅ Student Match Found");
    } else {
      uiLog(
        `face-match WARNING: best match is ${matchedId} ` +
        `(${matched.first_name} ${matched.surname}), distance=${distance}, ` +
        `but current card is ${currentId}.`
      );
      notifyToast("⚠️ No Match Found for this student photo");
    }
  } catch (err) {
    uiLog(`face-match exception: ${err.message || err}`);
    notifyToast("Face-match request failed (network / backend error).");
  }
}

// ---- 6. Handler for the Load button --------------------------------------

async function onLoadClicked() {
  const idInput = document.getElementById("studentIdInput");
  if (!idInput) {
    alert("Student ID input not found in the page.");
    return;
  }

  const raw = idInput.value.trim();
  if (!raw) {
    alert("Please type a student ID or full name (e.g. '32000025' or 'Aisha Taylor').");
    return;
  }

  const student = findStudentByInput(raw);

  if (!student) {
    alert(`No student found for "${raw}". Try numeric ID (e.g. 32000025) or full name.`);
    uiLog(`[WARN] No student found for search: "${raw}".`);
    return;
  }

  uiLog(
    `[load] Found student ${student.student_id} ` +
    `(${student.first_name} ${student.surname}) using search "${raw}".`
  );

  // Update UI
  fillFormFromStudent(student);
  updateCardPreview(student);

  // *** IMPORTANT: AI now loops through ALL stored faces automatically
  // via the backend, and we show toast "Match Found" / "No Match Found".
  await runFaceMatchForStudent(student);
}

// ---- 7. Initialise on page load -----------------------------------------

document.addEventListener("DOMContentLoaded", async () => {
  await loadStudentsDataset();

  const btn = document.getElementById("loadStudentBtn");
  if (btn) {
    btn.addEventListener("click", onLoadClicked);
  } else {
    console.warn("loadStudentBtn not found in DOM.");
  }
});

