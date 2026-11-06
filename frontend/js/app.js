/**
 * Vaani Clinical (वाणी) — Telemetry & Triage Workstation Application
 * Real-time Clinical Telephony, OLD CARTS HPI reasoning, ECG cardiac waveform,
 * LOINC lab biomarker extraction, SOAP note synthesis, and HL7 FHIR v4 bundles.
 */

// Application State
const state = {
  encounterId: "ENC-" + Math.floor(10000 + Math.random() * 90000),
  patientProfile: {
    name: "Robert Vance",
    age: 62,
    biological_sex: "male",
    mrn: "MRN-CV-88219",
    allergies: ["Penicillin (anaphylaxis)"],
    current_medications: ["Atorvastatin 40mg", "Metoprolol 50mg", "Lisinopril 10mg"],
    past_medical_history: ["Hypertension", "Hyperlipidemia", "Tobacco use (30 pack-years)"]
  },
  dialogueHistory: [],
  currentHPI: {},
  latestAssessment: null,
  extractedBiomarkers: [],
  ttsActive: true,
  lastSoapNote: null,
  lastFhirBundle: null
};

// DOM Elements
const el = {
  clockDisplay: document.getElementById("clockDisplay"),
  hudPatientName: document.getElementById("hudPatientName"),
  hudPatientMRN: document.getElementById("hudPatientMRN"),
  hudDemographics: document.getElementById("hudDemographics"),
  currentEncounterId: document.getElementById("currentEncounterId"),
  dialogueStream: document.getElementById("dialogueStream"),
  chatForm: document.getElementById("chatForm"),
  patientInput: document.getElementById("patientInput"),
  ttsToggleBtn: document.getElementById("ttsToggleBtn"),
  ttsIcon: document.getElementById("ttsIcon"),
  ttsStatus: document.getElementById("ttsStatus"),
  micSimBtn: document.getElementById("micSimBtn"),
  resetCallBtn: document.getElementById("resetCallBtn"),
  emergencyBanner: document.getElementById("emergencyBanner"),
  emergencyTitle: document.getElementById("emergencyTitle"),
  emergencyAction: document.getElementById("emergencyAction"),
  escalate911Btn: document.getElementById("escalate911Btn"),
  esiBadgeDisplay: document.getElementById("esiBadgeDisplay"),
  esiDispositionText: document.getElementById("esiDispositionText"),
  triagePhaseBadge: document.getElementById("triagePhaseBadge"),
  diffListContainer: document.getElementById("diffListContainer"),
  // OLD CARTS Elements
  oldcartOnset: document.getElementById("oldcartOnset"),
  oldcartLocation: document.getElementById("oldcartLocation"),
  oldcartDuration: document.getElementById("oldcartDuration"),
  oldcartCharacter: document.getElementById("oldcartCharacter"),
  oldcartAggravating: document.getElementById("oldcartAggravating"),
  oldcartRelieving: document.getElementById("oldcartRelieving"),
  oldcartRadiation: document.getElementById("oldcartRadiation"),
  oldcartSeverity: document.getElementById("oldcartSeverity"),
  // SOAP Studio
  generateSoapBtn: document.getElementById("generateSoapBtn"),
  copySoapBtn: document.getElementById("copySoapBtn"),
  soapRenderedContent: document.getElementById("soapRenderedContent"),
  // Biomarkers Lab
  labInputText: document.getElementById("labInputText"),
  pasteSampleLabBtn: document.getElementById("pasteSampleLabBtn"),
  extractLabBtn: document.getElementById("extractLabBtn"),
  biomarkerTableBody: document.getElementById("biomarkerTableBody"),
  bioOrganAlertCount: document.getElementById("bioOrganAlertCount"),
  // FHIR Explorer
  generateFhirBtn: document.getElementById("generateFhirBtn"),
  downloadFhirBtn: document.getElementById("downloadFhirBtn"),
  fhirCodeView: document.getElementById("fhirCodeView"),
  // Clinical Simulator
  scenariosGrid: document.getElementById("scenariosGrid"),
  // Canvases
  ecgCanvas: document.getElementById("ecgCanvas"),
  audioVisCanvas: document.getElementById("audioVisCanvas")
};


// --- INITIALIZATION ---
window.addEventListener("DOMContentLoaded", () => {
  initClock();
  initTabNavigation();
  initECGMonitor();
  initAudioVisualizer();
  initEventHandlers();
  loadPresetScenarios();
  updatePatientHUD();
});


// --- DIGITAL CLOCK ---
function initClock() {
  function tick() {
    const now = new Date();
    const h = String(now.getUTCHours()).padStart(2, '0');
    const m = String(now.getUTCMinutes()).padStart(2, '0');
    const s = String(now.getUTCSeconds()).padStart(2, '0');
    if (el.clockDisplay) {
      el.clockDisplay.textContent = `${h}:${m}:${s} UTC`;
    }
  }
  tick();
  setInterval(tick, 1000);
}


// --- TAB NAVIGATION ---
function initTabNavigation() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-target");
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".workspace-panel").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add("active");
      }
    });
  });
}


// --- PATIENT HUD UPDATE ---
function updatePatientHUD() {
  if (el.hudPatientName) el.hudPatientName.textContent = state.patientProfile.name;
  if (el.hudPatientMRN) el.hudPatientMRN.textContent = state.patientProfile.mrn;
  if (el.currentEncounterId) el.currentEncounterId.textContent = state.encounterId;

  const ageSex = `${state.patientProfile.age || 'Unspecified'} yo • ${state.patientProfile.biological_sex.toUpperCase()}`;
  const allergies = state.patientProfile.allergies.length 
    ? `Allergies: ${state.patientProfile.allergies.join(', ')}`
    : 'No known drug allergies';
  if (el.hudDemographics) el.hudDemographics.textContent = `${ageSex} • ${allergies}`;
}


// --- REAL-TIME ECG CARDIAC WAVEFORM MONITOR ---
function initECGMonitor() {
  const canvas = el.ecgCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resizeCanvas() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;
  }
  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);

  let x = 0;
  let prevY = canvas.height / 2;
  let heartRate = 88;
  let cycle = 0;

  function getEcgY(t) {
    const baseline = canvas.height / 2;
    const normT = (t % 100) / 100; // 0 to 1 cycle

    // P-Q-R-S-T wave model
    if (normT > 0.15 && normT < 0.22) {
      // P wave
      return baseline - Math.sin((normT - 0.15) / 0.07 * Math.PI) * 4;
    } else if (normT >= 0.28 && normT < 0.30) {
      // Q dip
      return baseline + 3;
    } else if (normT >= 0.30 && normT < 0.34) {
      // R spike
      return baseline - 24;
    } else if (normT >= 0.34 && normT < 0.37) {
      // S dip
      return baseline + 7;
    } else if (normT > 0.48 && normT < 0.62) {
      // T wave
      return baseline - Math.sin((normT - 0.48) / 0.14 * Math.PI) * 6;
    }
    return baseline + (Math.random() - 0.5) * 1.2; // subtle noise
  }

  function drawECG() {
    // Clear sweep beam
    ctx.fillStyle = "rgba(4, 6, 9, 0.08)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Subtle grid lines
    ctx.strokeStyle = "rgba(20, 28, 44, 0.4)";
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    for (let gy = 0; gy < canvas.height; gy += 12) {
      ctx.moveTo(0, gy);
      ctx.lineTo(canvas.width, gy);
    }
    ctx.stroke();

    const speed = 2.2;
    const y = getEcgY(cycle);

    // Green ECG trace with neon glow
    ctx.shadowBlur = 8;
    ctx.shadowColor = "#00e599";
    ctx.strokeStyle = "#00ffaa";
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    ctx.moveTo(x, prevY);
    ctx.lineTo(x + speed, y);
    ctx.stroke();

    ctx.shadowBlur = 0; // reset shadow
    prevY = y;
    x += speed;
    cycle += 1.3;

    if (x >= canvas.width) {
      x = 0;
      prevY = canvas.height / 2;
    }

    requestAnimationFrame(drawECG);
  }

  drawECG();
}


// --- AUDIO FREQUENCY VISUALIZER ---
let audioActive = false;
function initAudioVisualizer() {
  const canvas = el.audioVisCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    canvas.width = canvas.parentElement.clientWidth - 32;
    canvas.height = 24;
  }
  resize();
  window.addEventListener("resize", resize);

  const numBars = 48;
  const barWidth = 3;

  function renderBars() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const spacing = canvas.width / numBars;

    for (let i = 0; i < numBars; i++) {
      let height = 3;
      if (audioActive) {
        height = 3 + Math.sin(Date.now() * 0.015 + i * 0.4) * 8 + Math.random() * 8;
      }
      ctx.fillStyle = audioActive ? "#00f0ff" : "#1a2234";
      ctx.fillRect(i * spacing, (canvas.height - height) / 2, barWidth, height);
    }
    requestAnimationFrame(renderBars);
  }
  renderBars();
}

function pulseAudioVis(durationMs = 2500) {
  audioActive = true;
  setTimeout(() => {
    audioActive = false;
  }, durationMs);
}


// --- SPEECH SYNTHESIS (TTS) ---
function speakText(text) {
  if (!state.ttsActive || !('speechSynthesis' in window)) return;
  try {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;
    
    // Pick clear English voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Samantha")));
    if (preferredVoice) utterance.voice = preferredVoice;

    pulseAudioVis(text.length * 55);
    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.warn("TTS playback error:", err);
  }
}


// --- EVENT HANDLERS ---
function initEventHandlers() {
  // TTS toggle
  el.ttsToggleBtn.addEventListener("click", () => {
    state.ttsActive = !state.ttsActive;
    if (state.ttsActive) {
      el.ttsIcon.textContent = "🔊";
      el.ttsStatus.textContent = "TTS: ACTIVE";
    } else {
      window.speechSynthesis.cancel();
      el.ttsIcon.textContent = "🔇";
      el.ttsStatus.textContent = "TTS: MUTED";
    }
  });

  // Chat form submit
  el.chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = el.patientInput.value.trim();
    if (!text) return;
    el.patientInput.value = "";
    sendPatientMessage(text);
  });

  // Simulate Mic voice prompt
  el.micSimBtn.addEventListener("click", () => {
    const prompts = [
      "I feel terrible crushing pressure in the middle of my chest radiating to my jaw, rated 8 out of 10.",
      "My speech is slurred and my right arm feels like dead weight since 30 minutes ago.",
      "I have type 1 diabetes and my blood sugar is over 500, with constant vomiting and fruity breath.",
      "I have a mild runny nose and slight scratchy throat since yesterday, no fever."
    ];
    const picked = prompts[Math.floor(Math.random() * prompts.length)];
    el.patientInput.value = picked;
    el.patientInput.focus();
  });

  // Reset call button
  el.resetCallBtn.addEventListener("click", () => {
    state.encounterId = "ENC-" + Math.floor(10000 + Math.random() * 90000);
    state.dialogueHistory = [];
    state.currentHPI = {};
    state.latestAssessment = null;
    state.extractedBiomarkers = [];
    updatePatientHUD();

    el.dialogueStream.innerHTML = `
      <div class="msg-row agent">
        <div class="msg-meta">VAANI CLINICAL AI RECEPTIONIST • INTAKE</div>
        <div class="msg-bubble">
          Hello, this is the Vaani Clinical Triage Service. I am an intelligent clinical receptionist. 
          Please describe what symptoms or medical emergency you are experiencing today.
        </div>
      </div>
    `;
    resetTriageHUD();
  });

  // Escalate 911 button
  el.escalate911Btn.addEventListener("click", () => {
    alert(`🚨 CODE RED DISPATCH INITIATED 🚨\n\nEmergency dispatch protocol activated for Encounter ${state.encounterId}.\nPatient: ${state.patientProfile.name} (MRN: ${state.patientProfile.mrn})\nDisposition: Immediate Resuscitation / EMS 911 Ambulance Dispatched.`);
  });

  // SOAP Studio buttons
  el.generateSoapBtn.addEventListener("click", generateSOAPNote);
  el.copySoapBtn.addEventListener("click", () => {
    if (state.lastSoapNote && state.lastSoapNote.markdown_formatted) {
      navigator.clipboard.writeText(state.lastSoapNote.markdown_formatted).then(() => {
        alert("SOAP Note Markdown copied to clipboard!");
      });
    } else {
      alert("Please synthesize a SOAP note first.");
    }
  });

  // Biomarker Lab buttons
  el.pasteSampleLabBtn.addEventListener("click", () => {
    el.labInputText.value = 
`Comprehensive Clinical Lab Panel:
Cardiac Troponin I: 1.45 ng/mL
BNP: 420 pg/mL
D-Dimer: 0.38 ug/mL FEU
Serum Fasting Glucose: 285 mg/dL
HbA1c: 9.8 %
Serum Creatinine: 2.1 mg/dL
eGFR: 42 mL/min/1.73m2
Serum Potassium: 5.6 mEq/L
Blood Hemoglobin: 13.8 g/dL
White Blood Cell: 12.8 x10^3/uL`;
  });

  el.extractLabBtn.addEventListener("click", () => {
    const raw = el.labInputText.value.trim();
    if (!raw) {
      alert("Please enter or paste clinical lab text.");
      return;
    }
    extractBiomarkersFromText(raw);
  });

  // FHIR Explorer buttons
  el.generateFhirBtn.addEventListener("click", compileFHIRBundle);
  el.downloadFhirBtn.addEventListener("click", () => {
    if (!state.lastFhirBundle) {
      alert("Compile FHIR bundle first.");
      return;
    }
    const blob = new Blob([JSON.stringify(state.lastFhirBundle.raw_fhir_json, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `FHIR_${state.encounterId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });
}


// --- SEND PATIENT MESSAGE TO BACKEND API ---
async function sendPatientMessage(text) {
  // Append patient bubble
  appendChatBubble("patient", text);
  pulseAudioVis(1200);

  try {
    const response = await fetch("/api/triage/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        encounter_id: state.encounterId,
        patient_message: text,
        patient_profile: state.patientProfile
      })
    });

    if (!response.ok) throw new Error("API error: " + response.statusText);
    const data = await response.json();

    // Append agent bubble with audio badge
    appendChatBubble("agent", data.agent_reply, data.agent_speech_text);

    // Speak audio text
    speakText(data.agent_speech_text);

    // Update state & UI
    state.latestAssessment = data.triage_assessment;
    state.currentHPI = data.triage_assessment.hpi;
    if (data.extracted_biomarkers) state.extractedBiomarkers = data.extracted_biomarkers;

    updateTriageHUD(data);

  } catch (err) {
    console.error("Triage message failed:", err);
    appendChatBubble("agent", "Error connecting to clinical triage server. Please verify backend service is running.");
  }
}


// --- CHAT STREAM BUBBLE BUILDER ---
function appendChatBubble(role, content, speechText = null) {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;

  const meta = document.createElement("div");
  meta.className = "msg-meta";
  meta.textContent = role === "patient" 
    ? `${state.patientProfile.name.toUpperCase()} (CALLER)`
    : "VAANI CLINICAL AI RECEPTIONIST";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = content.replace(/\n/g, "<br>");

  if (speechText) {
    const audioBar = document.createElement("div");
    audioBar.className = "msg-bubble-audio";
    audioBar.innerHTML = `
      <span>🔊 TTS Speech Generated</span>
      <button class="play-speech-btn">PLAY AGAIN</button>
    `;
    audioBar.querySelector(".play-speech-btn").addEventListener("click", () => {
      speakText(speechText);
    });
    bubble.appendChild(audioBar);
  }

  row.appendChild(meta);
  row.appendChild(bubble);
  el.dialogueStream.appendChild(row);
  el.dialogueStream.scrollTop = el.dialogueStream.scrollHeight;
}


// --- UPDATE TRIAGE HUD WITH ASSESSMENT ---
function updateTriageHUD(data) {
  const assess = data.triage_assessment;
  const hpi = assess.hpi;

  // ESI Badge
  el.esiBadgeDisplay.className = `esi-badge esi-${assess.esi_level}`;
  el.esiBadgeDisplay.textContent = assess.triage_status;
  el.esiDispositionText.textContent = assess.recommended_disposition;
  el.triagePhaseBadge.textContent = data.current_phase;

  // Emergency banner
  if (data.has_critical_red_flag) {
    el.emergencyBanner.classList.remove("hidden");
    const topFlag = assess.red_flags[0];
    if (topFlag) {
      el.emergencyTitle.textContent = `CRITICAL ALERT: ${topFlag.clinical_risk.toUpperCase()}`;
      el.emergencyAction.textContent = topFlag.immediate_action;
    }
  } else {
    el.emergencyBanner.classList.add("hidden");
  }

  // OLD CARTS parameter update
  setOldcartVal(el.oldcartOnset, hpi.onset);
  setOldcartVal(el.oldcartLocation, hpi.location);
  setOldcartVal(el.oldcartDuration, hpi.duration);
  setOldcartVal(el.oldcartCharacter, hpi.character);
  setOldcartVal(el.oldcartAggravating, hpi.aggravating);
  setOldcartVal(el.oldcartRelieving, hpi.relieving);
  setOldcartVal(el.oldcartRadiation, hpi.radiation);
  if (hpi.severity !== null && hpi.severity !== undefined) {
    el.oldcartSeverity.textContent = `${hpi.severity} / 10`;
    el.oldcartSeverity.classList.remove("empty");
  } else {
    el.oldcartSeverity.textContent = "-- / 10";
    el.oldcartSeverity.classList.add("empty");
  }

  // Differentials
  el.diffListContainer.innerHTML = "";
  if (assess.differentials && assess.differentials.length > 0) {
    assess.differentials.forEach(diff => {
      const item = document.createElement("div");
      item.className = "diff-item";
      item.innerHTML = `
        <div class="diff-header">
          <span>${diff.condition_name}</span>
          <span class="diff-icd">${diff.icd10_code}</span>
        </div>
        <div class="diff-meta">
          <strong>Probability: ${diff.probability}</strong> • ${diff.justification}
        </div>
      `;
      el.diffListContainer.appendChild(item);
    });
  }

  // Update biomarker table if newly parsed
  if (data.extracted_biomarkers && data.extracted_biomarkers.length > 0) {
    renderBiomarkerTable(data.extracted_biomarkers);
  }
}

function setOldcartVal(elem, value) {
  if (!elem) return;
  if (value) {
    elem.textContent = value;
    elem.classList.remove("empty");
  } else {
    elem.textContent = "Pending...";
    elem.classList.add("empty");
  }
}

function resetTriageHUD() {
  el.esiBadgeDisplay.className = "esi-badge esi-3";
  el.esiBadgeDisplay.textContent = "ESI-3 URGENT";
  el.esiDispositionText.textContent = "Awaiting clinical symptom assessment and OLD CARTS parameters.";
  el.triagePhaseBadge.textContent = "INTAKE";
  el.emergencyBanner.classList.add("hidden");

  ["Onset", "Location", "Duration", "Character", "Aggravating", "Relieving", "Radiation"].forEach(key => {
    setOldcartVal(el[`oldcart${key}`], null);
  });
  el.oldcartSeverity.textContent = "-- / 10";
  el.oldcartSeverity.classList.add("empty");

  el.diffListContainer.innerHTML = `
    <div class="diff-item">
      <div class="diff-header">
        <span>Awaiting symptom report</span>
        <span class="diff-icd">Z00.00</span>
      </div>
      <div class="diff-meta">Start dialogue to generate differentials.</div>
    </div>
  `;
}


// --- SOAP NOTE SYNTHESIS ---
async function generateSOAPNote() {
  if (!state.latestAssessment) {
    alert("Please conduct a triage intake first so clinical parameters are present.");
    return;
  }

  try {
    const payload = {
      encounter_id: state.encounterId,
      patient_profile: state.patientProfile,
      assessment: state.latestAssessment,
      biomarkers: state.extractedBiomarkers,
      vitals: {
        blood_pressure: "152/94 mmHg",
        heart_rate_bpm: 88,
        spo2_percent: 96,
        respiratory_rate: 22,
        temperature_c: 37.2
      },
      telemetry_findings: "Telemetry shows sinus tachycardia with lead II ST segment elevation."
    };

    const res = await fetch("/api/triage/soap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("SOAP synthesis failed: " + res.statusText);
    const note = await res.json();
    state.lastSoapNote = note;

    // Render markdown
    if (typeof marked !== "undefined") {
      el.soapRenderedContent.innerHTML = marked.parse(note.markdown_formatted);
    } else {
      el.soapRenderedContent.innerText = note.markdown_formatted;
    }

  } catch (err) {
    console.error("SOAP note error:", err);
    alert("Error generating SOAP note: " + err.message);
  }
}


// --- BIOMARKER LAB EXTRACTION (Sehatlings-Muaina Inspiration) ---
async function extractBiomarkersFromText(clinicalText) {
  try {
    const res = await fetch("/api/triage/biomarkers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        encounter_id: state.encounterId,
        clinical_text: clinicalText
      })
    });

    if (!res.ok) throw new Error("Biomarker extraction failed");
    const data = await res.json();

    state.extractedBiomarkers = data.biomarkers;
    renderBiomarkerTable(data.biomarkers);

    el.bioOrganAlertCount.textContent = `${data.critical_count} Critical Alert(s)`;
    el.bioOrganAlertCount.style.color = data.critical_count > 0 ? "var(--neon-red)" : "var(--neon-green)";

  } catch (err) {
    console.error("Biomarker lab error:", err);
    alert("Biomarker extraction error: " + err.message);
  }
}

function renderBiomarkerTable(biomarkers) {
  if (!el.biomarkerTableBody) return;
  if (!biomarkers || biomarkers.length === 0) {
    el.biomarkerTableBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; color: var(--text-dim); padding: 24px;">
          No biomarkers parsed.
        </td>
      </tr>
    `;
    return;
  }

  el.biomarkerTableBody.innerHTML = "";
  biomarkers.forEach(b => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${b.name}</strong> (${b.test_code})</td>
      <td><code>${b.loinc_code}</code></td>
      <td><strong style="color: #fff;">${b.value} ${b.unit}</strong></td>
      <td style="color: var(--text-muted);">${b.reference_low} – ${b.reference_high} ${b.unit}</td>
      <td><span class="bio-status-badge bio-status-${b.status}">${b.status}</span></td>
      <td style="font-size: 12px; color: #cbd5e1;">${b.clinical_interpretation}</td>
    `;
    el.biomarkerTableBody.appendChild(tr);
  });
}


// --- HL7 FHIR RELEASE 4 COMPILATION ---
async function compileFHIRBundle() {
  if (!state.latestAssessment) {
    alert("Please initiate a clinical encounter or scenario first.");
    return;
  }

  try {
    const payload = {
      encounter_id: state.encounterId,
      patient_profile: state.patientProfile,
      assessment: state.latestAssessment,
      biomarkers: state.extractedBiomarkers,
      soap_note: state.lastSoapNote
    };

    const res = await fetch("/api/triage/fhir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("FHIR compilation failed");
    const bundle = await res.json();
    state.lastFhirBundle = bundle;

    el.fhirCodeView.textContent = JSON.stringify(bundle.raw_fhir_json, null, 2);

  } catch (err) {
    console.error("FHIR error:", err);
    alert("FHIR generation error: " + err.message);
  }
}


// --- PRESET SCENARIO LOADER ---
async function loadPresetScenarios() {
  try {
    const res = await fetch("/api/scenarios");
    if (!res.ok) throw new Error("Could not fetch scenarios");
    const scenarios = await res.json();

    if (!el.scenariosGrid) return;
    el.scenariosGrid.innerHTML = "";

    scenarios.forEach(sc => {
      const card = document.createElement("div");
      card.className = "scenario-card";
      card.innerHTML = `
        <div class="scenario-badge-row">
          <span style="font-family: var(--font-mono); font-size: 11px; color: var(--neon-cyan);">${sc.specialty}</span>
          <span class="esi-badge esi-${sc.esi_level}" style="font-size: 11px; padding: 2px 8px;">ESI-${sc.esi_level}</span>
        </div>
        <div class="scenario-title">${sc.title}</div>
        <div class="scenario-desc">${sc.chief_complaint}</div>
        <div style="font-size: 11px; color: var(--text-dim); font-family: var(--font-mono);">
          Patient: ${sc.patient_profile.name} (${sc.patient_profile.age} yo ${sc.patient_profile.biological_sex})
        </div>
        <button class="btn-ctrl" style="margin-top: 8px; justify-content: center; color: var(--neon-cyan);">
          ▶ LOAD & EXECUTE SCENARIO
        </button>
      `;

      card.addEventListener("click", () => {
        applyScenario(sc);
      });

      el.scenariosGrid.appendChild(card);
    });

  } catch (err) {
    console.error("Scenarios load failed:", err);
  }
}

async function applyScenario(sc) {
  // Update state
  state.encounterId = "ENC-" + Math.floor(10000 + Math.random() * 90000);
  state.patientProfile = sc.patient_profile;
  state.dialogueHistory = [];
  updatePatientHUD();

  // Reset chat view
  el.dialogueStream.innerHTML = `
    <div class="msg-row agent">
      <div class="msg-meta">VAANI CLINICAL AI RECEPTIONIST • INTAKE</div>
      <div class="msg-bubble">
        Hello, this is the Vaani Clinical Triage Service. I am an intelligent clinical receptionist. 
        Please describe what symptoms or medical emergency you are experiencing today.
      </div>
    </div>
  `;

  // Switch to Workspace 1
  document.querySelector('[data-target="workspace-triage"]').click();

  // Send sample messages in sequence
  for (const msg of sc.sample_dialogue) {
    await sendPatientMessage(msg.content);
    await new Promise(r => setTimeout(r, 600));
  }

  // If scenario has lab text, populate Biomarker Lab and extract
  if (sc.lab_text_snippet) {
    el.labInputText.value = sc.lab_text_snippet;
    await extractBiomarkersFromText(sc.lab_text_snippet);
  }

  // Automatically synthesize SOAP and FHIR bundle for the scenario
  setTimeout(async () => {
    await generateSOAPNote();
    await compileFHIRBundle();
  }, 800);
}
