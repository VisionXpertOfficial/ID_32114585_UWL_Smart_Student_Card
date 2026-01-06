// ui/app.js

// ---------- Config ----------
const GATEWAY = `http://${window.location.hostname}:8099`; // works in Edge/Chrome/localhost/127.0.0.1
const FACE_API = `http://${window.location.hostname}:5000`; // Flask backend for face-match

// ---------- DOM ----------
const els = {
  hour:          document.getElementById("hour"),
  dist_km:       document.getElementById("dist_km"),
  fail_cnt:      document.getElementById("fail_cnt"),
  device_change: document.getElementById("device_change"),

  btnConsent: document.getElementById("btn-consent"),
  btnVerify:  document.getElementById("btn-verify"),
  btnLogs:    document.getElementById("btn-logs"),

  logs: document.getElementById("logs"),

  card:        document.querySelector(".card"),
  badge:       document.querySelector(".badge"),
  verdictLine: document.getElementById("card_verdict") || (() => {
                 const p = document.createElement("div");
                 p.className = "meta verdict";
                 p.id = "card_verdict";
                 const meta = document.querySelector(".card .meta");
                 meta.appendChild(p);
                 return p;
               })(),

  historyWrap: document.getElementById("score_history_wrap") || document.querySelector(".history"),
  resetBtn:    document.getElementById("btn-reset-history")  || document.querySelector(".btn-reset-history")
};

// local “sparkline” history (scores)
const SCORE_KEY = "scoreHistory";

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(SCORE_KEY) || "[]"); }
  catch (e) { return []; }
}
function saveHistory(arr) {
  localStorage.setItem(SCORE_KEY, JSON.stringify(arr.slice(-40)));
}
function resetHistory() {
  localStorage.removeItem(SCORE_KEY);
  drawHistory([]);
}

// very tiny spark “chart”
function drawHistory(values) {
  const host = document.querySelector(".history-plot");
  if (!host) return;
  host.innerHTML = "";
  const MAX = 1;
  const W = host.clientWidth || 280;
  const H = host.clientHeight || 40;
  const n = Math.min(values.length, 40);
  const step = Math.max(1, Math.floor(W / Math.max(1, n)));

  for (let i = 0; i < n; i++) {
    const v = values[values.length - n + i];
    const h = Math.max(2, Math.round((v / MAX) * (H - 2)));
    const bar = document.createElement("div");
    bar.style.cssText =
      `display:inline-block;width:${step-2}px;height:${h}px;` +
      `margin:0 1px;vertical-align:bottom;border-radius:2px;` +
      `background:${v<0.33?'#2fbf71':v<0.66?'#f4a300':'#d64545'};`;
    host.appendChild(bar);
  }
}

// ---------- Toast + highlight ----------
function showToast(msg) {
  let t = document.getElementById("toast");
  if (!t) {
    t = document.createElement("div");
    t.id = "toast";
    t.className = "toast";
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.add("toast--visible");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => {
    t.classList.remove("toast--visible");
  }, 2500);
}

function highlightCard() {
  els.card.classList.add("card--highlight");
  setTimeout(() => els.card.classList.remove("card--highlight"), 500);
}

// ---------- Badge / card states ----------
function setBadge(colorClass, text, hint, borderColor) {
  els.badge.classList.remove(
    "badge-neutral",
    "badge--ok",
    "badge--warn",
    "badge--danger",
    "badge--consent"
  );
  els.badge.classList.add(colorClass);
  els.badge.textContent = text;
  els.verdictLine.textContent = hint || "";
  els.card.style.boxShadow = borderColor
    ? `0 0 0 3px ${borderColor} inset, 0 8px 28px rgba(0,0,0,.35)`
    : `0 8px 28px rgba(0,0,0,.35)`;
}

function setPending(msg) {
  setBadge(
    "badge-neutral",
    "Student",
    msg || "Awaiting AI verification",
    null
  );
}

function setSafe(score, msg) {
  setBadge(
    "badge--ok",
    "Student ✓",
    msg || `AI: looks normal (score ${(score * 100).toFixed(1)}%)`,
    "rgba(47,191,113,.45)"
  );
}

function setDecline(reason) {
  setBadge(
    "badge--danger",
    "Student ✗",
    reason || "Declined by AI",
    "rgba(214,69,69,.45)"
  );
}

function setConsentActive() {
  const ts = new Date().toTimeString().slice(0,5);
  setBadge(
    "badge--consent",
    "Student ✓",
    `Consent active (set at ${ts})`,
    "rgba(30,102,255,.45)"
  );
}

// ---------- Logging ----------
function logLine(s) {
  const ts = new Date().toTimeString().slice(0,8);
  els.logs.value += `[${ts}] ${s}\n`;
  els.logs.scrollTop = els.logs.scrollHeight;
}

// ---------- Helper: get current photo filename ----------
function getCurrentPhotoFilename() {
  // card image: <img class="photo" src="assets/32000025_Aisha_Taylor.png">
  const img = document.querySelector(".card .photo");
  if (!img) return null;

  const src = img.getAttribute("src") || "";
  // take the last part like "32000025_Aisha_Taylor.png"
  const match = src.match(/([^\/\\]+\.png)(?:\?|$)/i);
  return match ? match[1] : null;
}

// ---------- Full reset ----------
function fullReset() {
  resetHistory();
  els.logs.value = "";
  setPending("Awaiting AI verification");
}

// ---------- Consent action ----------
async function sendConsent() {
  setConsentActive();
  logLine("consent set: true");

  const url = `${GATEWAY}/consent`;
  logLine(`POST ${url} {"consent":true}`);
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ consent: true })
    });
    const text = await resp.text();
    logLine(`consent resp: ${resp.status} ${text}`);
    showToast("Consent recorded");
    highlightCard();
  } catch (e) {
    logLine(`consent error: ${e.message || e}`);
    showToast("Consent saved locally (gateway offline)");
    highlightCard();
  }
}

// ---------- Face verification (Flask /face-match) ----------
async function verifyFaceMatch() {
  const filename = getCurrentPhotoFilename();

  if (!filename || filename === "student_photo.png") {
    logLine("face-match: no personalised student photo loaded; skipping face verification.");
    return;
  }

  const url = `${FACE_API}/face-match`;
  logLine(`face-match: POST ${url} {"filename":"${filename}"}`);

  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename })
    });

    let data = null;
    try { data = await resp.json(); } catch (e) {}

    if (!resp.ok) {
      logLine(`face-match ERROR ${resp.status}: ${JSON.stringify(data)}`);
      showToast("Face verification error");
      return;
    }

    if (data && data.error) {
      logLine(`face-match server error: ${data.error}`);
      showToast("Face verification could not complete");
      return;
    }

    const matchId  = data.student_id;
    const student  = data.student || {};
    const fullName = `${(student.first_name || "").trim()} ${(student.surname || "").trim()}`.trim();
    const distance = typeof data.distance === "number"
      ? data.distance.toFixed(3)
      : "n/a";

    const formId = (document.getElementById("studentIdInput")?.value || "").trim();

    if (matchId && formId && matchId === formId) {
      logLine(`face-match OK: image matches student ${matchId} (${fullName}), distance=${distance}`);
      showToast("Face matches this student ID");
    } else {
      logLine(
        `face-match WARNING: image belongs to ${matchId || "unknown"} (${fullName || "?"}), `
        + `distance=${distance}, current ID=${formId || "n/a"}`
      );
      // just a warning in logs – we do NOT change badge colours
      showToast("Face does not match current student ID (see logs)");
    }

  } catch (e) {
    logLine(`face-match EXCEPTION: ${e.message || e}`);
    showToast("Face verification failed (network error)");
  }
}

// ---------- Verify with AI (original + face logs) ----------
async function verify() {
  setPending("Checking with AI ...");

  const payload = {
    hour:          Number(els.hour.value),
    dist_km:       Number(els.dist_km.value),
    fail_cnt:      Number(els.fail_cnt.value),
    device_change: Number(els.device_change.value)
  };

  const url = `${GATEWAY}/verify`;
  logLine(`POST ${url} ${JSON.stringify(payload)}`);

  els.btnVerify.disabled = true;
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });

    let data = null;
    try { data = await resp.json(); } catch (e) {}

    // DEMO: if gateway errors, still approve
    if (!resp.ok) {
      logLine(`ERROR ${resp.status}: ${JSON.stringify(data)}`);
      setSafe(0.88, "Temporarily approved — verification service error");
      highlightCard();
      showToast("Verification service error — temporary approval");

      // even if gateway fails, you can still log face check
      await verifyFaceMatch();
      return;
    }

    logLine(`OK ${resp.status}: ${JSON.stringify(data)}`);

    if (typeof data?.anomaly !== "undefined" && typeof data?.score !== "undefined") {
      const anomaly = !!data.anomaly;
      const score   = Number(data.score);

      const hist = loadHistory();
      hist.push(score);
      saveHistory(hist);
      drawHistory(hist);

      if (anomaly) {
        setDecline("Declined by AI");
        showToast("AI flagged this as anomalous");
      } else {
        setSafe(score);
        showToast("Verified by AI");
      }
      highlightCard();
    } else {
      setSafe(0.9, "Temporarily approved — unexpected response");
      highlightCard();
      showToast("Unexpected response — temporary approval");
    }

    // 🔹 NEW: after behavioural check, also do face recognition (logs only)
    await verifyFaceMatch();

  } catch (e) {
    logLine(`EXCEPTION: ${e.message || e}`);
    setSafe(0.92, "Temporarily approved — system offline");
    highlightCard();
    showToast("Gateway offline — temporary approval");

    // still try face logging
    await verifyFaceMatch();
  } finally {
    els.btnVerify.disabled = false;
  }
}

// ---------- Fetch logs ----------
async function fetchLogs() {
  const url = `${GATEWAY}/logs`;
  logLine(`fetch logs: ${url}`);
  try {
    const resp = await fetch(url);
    const text = await resp.text();
    logLine(text ? text.slice(-400) : "(no logs)");
    showToast("System logs retrieved");
    highlightCard();
  } catch (e) {
    logLine("fetch logs: failed: " + e.message);
    showToast("Failed to fetch logs (gateway offline)");
  }
}

// ---------- Wire-up ----------
function init() {
  setPending();
  drawHistory(loadHistory());

  els.btnVerify.addEventListener("click", verify);
  els.btnLogs?.addEventListener("click", fetchLogs);
  els.btnConsent?.addEventListener("click", sendConsent);
  els.resetBtn?.addEventListener("click", fullReset);
}

document.addEventListener("DOMContentLoaded", init);






