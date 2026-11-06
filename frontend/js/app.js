/**
 * Vaani Clinical (वाणी) — Telemetry & Triage Workstation Application
 * Real-time Clinical Telephony, OLD CARTS HPI reasoning, Arrhythmia ECG canvas,
 * LOINC lab biomarker extraction, SOAP note synthesis, HL7 FHIR v4 bundles,
 * HEART / Wells / qSOFA / GCS calculators, RxNorm drug safety, and Linked Evidence grounding.
 */

// Application State
const state = {
  encounterId: "ENC-" + Math.floor(10000 + Math.random() * 90000),
  patientProfile: {
    name: "Robert Vance",
    age: 62,
    biological_sex: "male",
    mrn: "MRN-CV-88219",
    allergies: ["Penicillin (anaphylaxis)", "Aspirin"],
    current_medications: ["Atorvastatin 40mg", "Metoprolol 50mg", "Lisinopril 10mg"],
    past_medical_history: ["Hypertension", "Hyperlipidemia", "Tobacco use (30 pack-years)"]
  },
  dialogueHistory: [],
  currentHPI: {},
  latestAssessment: null,
  extractedBiomarkers: [],
  ttsActive: true,
  lastSoapNote: null,
  lastFhirBundle: null,
  lastAvs: null,
  // ECG & Arrhythmia simulation
  currentRhythm: "TACHY",
  heartRate: 118,
  // Audio & Speech recognition
  isLiveMicActive: false,
  speechRecognizer: null,
  audioContext: null,
  analyserNode: null,
  micStream: null
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
  liveMicBtn: document.getElementById("liveMicBtn"),
  micStatus: document.getElementById("micStatus"),
  dtmfToggleBtn: document.getElementById("dtmfToggleBtn"),
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
  auditGroundingBtn: document.getElementById("auditGroundingBtn"),
  soapRenderedContent: document.getElementById("soapRenderedContent"),
  evidenceListContainer: document.getElementById("evidenceListContainer"),
  evidenceScoreBadge: document.getElementById("evidenceScoreBadge"),
  // Biomarkers Lab
  labInputText: document.getElementById("labInputText"),
  pasteSampleLabBtn: document.getElementById("pasteSampleLabBtn"),
  extractLabBtn: document.getElementById("extractLabBtn"),
  biomarkerTableBody: document.getElementById("biomarkerTableBody"),
  bioOrganAlertCount: document.getElementById("bioOrganAlertCount"),
  // Calculators & Rx Safety
  calcHeartBtn: document.getElementById("calcHeartBtn"),
  calcWellsBtn: document.getElementById("calcWellsBtn"),
  calcQsofaBtn: document.getElementById("calcQsofaBtn"),
  calcGcsBtn: document.getElementById("calcGcsBtn"),
  runRxCheckBtn: document.getElementById("runRxCheckBtn"),
  rxAllergiesInput: document.getElementById("rxAllergiesInput"),
  rxProposedInput: document.getElementById("rxProposedInput"),
  rxAlertsList: document.getElementById("rxAlertsList"),
  // AVS & Printable Chart
  generateAvsBtn: document.getElementById("generateAvsBtn"),
  openPrintChartBtn: document.getElementById("openPrintChartBtn"),
  avsRenderedContent: document.getElementById("avsRenderedContent"),
  chartModalOverlay: document.getElementById("chartModalOverlay"),
  closeModalBtn: document.getElementById("closeModalBtn"),
  printModalBtn: document.getElementById("printModalBtn"),
  printableChartBody: document.getElementById("printableChartBody"),
  // DTMF Modal
  dtmfModalOverlay: document.getElementById("dtmfModalOverlay"),
  closeDtmfBtn: document.getElementById("closeDtmfBtn"),
  dtmfNumberDisplay: document.getElementById("dtmfNumberDisplay"),
  // FHIR Explorer
  generateFhirBtn: document.getElementById("generateFhirBtn"),
  downloadFhirBtn: document.getElementById("downloadFhirBtn"),
  fhirCodeView: document.getElementById("fhirCodeView"),
  // Clinical Simulator
  scenariosGrid: document.getElementById("scenariosGrid"),
  // Canvases & Telemetry Controls
  ecgCanvas: document.getElementById("ecgCanvas"),
  audioVisCanvas: document.getElementById("audioVisCanvas"),
  vuMeterText: document.getElementById("vuMeterText"),
  ecgHeartRate: document.getElementById("ecgHeartRate"),
  ecgRhythm: document.getElementById("ecgRhythm"),
  hrRangeSlider: document.getElementById("hrRangeSlider"),
  hrSliderVal: document.getElementById("hrSliderVal")
};


// --- INITIALIZATION ---
window.addEventListener("DOMContentLoaded", () => {
  initClock();
  initTabNavigation();
  initECGMonitor();
  initAudioVisualizer();
  initTelephonySound();
  initSpeechRecognition();
  initEventHandlers();
  loadPresetScenarios();
  updatePatientHUD();

  // Run initial calculator & safety checks
  runHeartScoreCalculation();
  runWellsPECalculation();
  runQsofaCalculation();
  runGcsCalculation();
  runRxSafetyCheck();
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
  if (el.rxAllergiesInput) el.rxAllergiesInput.value = state.patientProfile.allergies.join(", ");
}


// --- ARRHYTHMIA & ECG CARDIAC WAVEFORM MONITOR ---
function initECGMonitor() {
  const canvas = el.ecgCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resizeCanvas() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = 54;
  }
  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);

  let x = 0;
  let prevY = canvas.height / 2;
  let cycle = 0;
  let afibNoisePhase = 0;

  // Rhythm selector event buttons
  document.querySelectorAll(".rhythm-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".rhythm-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const r = btn.getAttribute("data-rhythm");
      const hr = parseInt(btn.getAttribute("data-hr"), 10);
      state.currentRhythm = r;
      state.heartRate = hr;

      el.ecgRhythm.textContent = btn.textContent;
      el.ecgHeartRate.textContent = hr > 0 ? `HR: ${hr} BPM` : "NO PULSE (ARREST)";
      el.hrRangeSlider.value = hr > 0 ? hr : 40;
      el.hrSliderVal.textContent = hr > 0 ? hr : "0";
    });
  });

  // HR Slider
  el.hrRangeSlider.addEventListener("input", (e) => {
    const val = parseInt(e.target.value, 10);
    state.heartRate = val;
    el.hrSliderVal.textContent = val;
    el.ecgHeartRate.textContent = `HR: ${val} BPM`;
  });

  function getEcgY(t, rhythm) {
    const baseline = canvas.height / 2;

    if (rhythm === "VFIB") {
      // Coarse Ventricular Fibrillation: chaotic sinusoidal arrest pattern
      return baseline + Math.sin(t * 0.12) * 14 + Math.sin(t * 0.28) * 8 + (Math.random() - 0.5) * 6;
    }

    const normT = (t % 100) / 100; // 0.0 to 1.0

    if (rhythm === "STEMI") {
      // Marked ST segment elevation (tombstone ST elevation)
      if (normT > 0.15 && normT < 0.22) {
        return baseline - Math.sin((normT - 0.15) / 0.07 * Math.PI) * 4; // P wave
      } else if (normT >= 0.28 && normT < 0.30) {
        return baseline + 3; // Q
      } else if (normT >= 0.30 && normT < 0.34) {
        return baseline - 24; // R spike
      } else if (normT >= 0.34 && normT < 0.37) {
        return baseline - 8; // Elevated ST takeoff
      } else if (normT >= 0.37 && normT < 0.65) {
        // High ST plateau + peaked T wave
        return baseline - 12 - Math.sin((normT - 0.37) / 0.28 * Math.PI) * 7;
      }
      return baseline;
    }

    if (rhythm === "AFIB") {
      // Atrial Fibrillation: No P waves, irregular baseline, random R spike intervals
      afibNoisePhase += 0.2;
      const fWaveNoise = Math.sin(afibNoisePhase * 3.4) * 2.2 + (Math.random() - 0.5) * 2.5;
      if (normT >= 0.30 && normT < 0.34) {
        return baseline - 22; // R spike
      } else if (normT >= 0.34 && normT < 0.37) {
        return baseline + 6; // S
      } else if (normT > 0.48 && normT < 0.62) {
        return baseline - Math.sin((normT - 0.48) / 0.14 * Math.PI) * 4 + fWaveNoise;
      }
      return baseline + fWaveNoise;
    }

    // Normal Sinus Rhythm (NSR) & Sinus Tachycardia (TACHY)
    if (normT > 0.15 && normT < 0.22) {
      return baseline - Math.sin((normT - 0.15) / 0.07 * Math.PI) * 4; // P wave
    } else if (normT >= 0.28 && normT < 0.30) {
      return baseline + 3; // Q
    } else if (normT >= 0.30 && normT < 0.34) {
      return baseline - 24; // R spike
    } else if (normT >= 0.34 && normT < 0.37) {
      return baseline + 7; // S
    } else if (normT > 0.48 && normT < 0.62) {
      return baseline - Math.sin((normT - 0.48) / 0.14 * Math.PI) * 6; // T wave
    }

    return baseline + (Math.random() - 0.5) * 1.0;
  }

  function drawECG() {
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

    const speed = 2.4;
    const y = getEcgY(cycle, state.currentRhythm);

    const isArrest = state.currentRhythm === "VFIB";
    ctx.shadowBlur = isArrest ? 12 : 8;
    ctx.shadowColor = isArrest ? "#ff2a55" : "#00e599";
    ctx.strokeStyle = isArrest ? "#ff3366" : "#00ffaa";
    ctx.lineWidth = 1.8;

    ctx.beginPath();
    ctx.moveTo(x, prevY);
    ctx.lineTo(x + speed, y);
    ctx.stroke();

    ctx.shadowBlur = 0;
    prevY = y;
    x += speed;

    const rateFactor = Math.max(0.4, (state.heartRate || 75) / 75);
    cycle += 1.3 * rateFactor;

    if (x >= canvas.width) {
      x = 0;
      prevY = canvas.height / 2;
    }

    requestAnimationFrame(drawECG);
  }

  drawECG();
}


// --- WEB AUDIO TELEPHONY & DTMF DUAL-TONE SYNTHESIZER ---
let webAudioCtx = null;
function getAudioContext() {
  if (!webAudioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      webAudioCtx = new AudioContextClass();
    }
  }
  if (webAudioCtx && webAudioCtx.state === "suspended") {
    webAudioCtx.resume();
  }
  return webAudioCtx;
}

// DTMF Frequency Map
const DTMF_FREQS = {
  "1": [697, 1209], "2": [697, 1336], "3": [697, 1477],
  "4": [770, 1209], "5": [770, 1336], "6": [770, 1477],
  "7": [852, 1209], "8": [852, 1336], "9": [852, 1477],
  "*": [941, 1209], "0": [941, 1336], "#": [941, 1477]
};

function playDTMFTone(key) {
  const actx = getAudioContext();
  if (!actx || !DTMF_FREQS[key]) return;

  const [f1, f2] = DTMF_FREQS[key];
  const osc1 = actx.createOscillator();
  const osc2 = actx.createOscillator();
  const gain = actx.createGain();

  osc1.frequency.value = f1;
  osc2.frequency.value = f2;
  gain.gain.setValueAtTime(0.12, actx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.0001, actx.currentTime + 0.18);

  osc1.connect(gain);
  osc2.connect(gain);
  gain.connect(actx.destination);

  osc1.start();
  osc2.start();
  osc1.stop(actx.currentTime + 0.18);
  osc2.stop(actx.currentTime + 0.18);
}

function initTelephonySound() {
  // DTMF buttons
  document.querySelectorAll(".dtmf-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const key = btn.getAttribute("data-key");
      playDTMFTone(key);
      if (el.dtmfNumberDisplay) {
        el.dtmfNumberDisplay.textContent += key;
      }
    });
  });

  if (el.dtmfToggleBtn) {
    el.dtmfToggleBtn.addEventListener("click", () => {
      el.dtmfNumberDisplay.textContent = "";
      el.dtmfModalOverlay.classList.add("active");
    });
  }
  if (el.closeDtmfBtn) {
    el.closeDtmfBtn.addEventListener("click", () => {
      el.dtmfModalOverlay.classList.remove("active");
    });
  }
}


// --- LIVE SPEECH RECOGNITION (WEB SPEECH API) ---
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    if (el.micStatus) el.micStatus.textContent = "MIC (NO BROWSER STT)";
    return;
  }

  const recognizer = new SpeechRecognition();
  recognizer.continuous = true;
  recognizer.interimResults = true;
  recognizer.lang = "en-US";

  recognizer.onstart = () => {
    state.isLiveMicActive = true;
    el.liveMicBtn.classList.add("active-mic");
    el.micStatus.textContent = "LISTENING LIVE...";
    startRealMicAnalyser();
  };

  recognizer.onresult = (event) => {
    let finalTranscript = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      }
    }
    if (finalTranscript.trim()) {
      el.patientInput.value = finalTranscript.trim();
      sendPatientMessage(finalTranscript.trim());
    }
  };

  recognizer.onerror = (e) => {
    console.warn("Speech recognition error:", e.error);
    stopLiveMic();
  };

  recognizer.onend = () => {
    if (state.isLiveMicActive) {
      try { recognizer.start(); } catch (_) {}
    } else {
      stopLiveMic();
    }
  };

  state.speechRecognizer = recognizer;

  el.liveMicBtn.addEventListener("click", () => {
    if (state.isLiveMicActive) {
      state.isLiveMicActive = false;
      recognizer.stop();
      stopLiveMic();
    } else {
      try {
        recognizer.start();
      } catch (err) {
        console.error("Mic start failed:", err);
      }
    }
  });
}

function stopLiveMic() {
  state.isLiveMicActive = false;
  el.liveMicBtn.classList.remove("active-mic");
  el.micStatus.textContent = "LIVE MIC STT";
  if (state.micStream) {
    state.micStream.getTracks().forEach(t => t.stop());
    state.micStream = null;
  }
}

async function startRealMicAnalyser() {
  try {
    const actx = getAudioContext();
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    state.micStream = stream;

    const source = actx.createMediaStreamSource(stream);
    const analyser = actx.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);
    state.analyserNode = analyser;
  } catch (err) {
    console.warn("Could not capture live microphone audio stream for VU meter:", err);
  }
}


// --- AUDIO FREQUENCY VISUALIZER & VU METER ---
let audioActive = false;
function initAudioVisualizer() {
  const canvas = el.audioVisCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    canvas.width = canvas.parentElement.clientWidth - 140;
    canvas.height = 22;
  }
  resize();
  window.addEventListener("resize", resize);

  const numBars = 36;
  const barWidth = 3;
  const freqData = new Uint8Array(32);

  function renderBars() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const spacing = canvas.width / numBars;

    let dbVal = -48;

    if (state.analyserNode && state.isLiveMicActive) {
      state.analyserNode.getByteFrequencyData(freqData);
      let sum = 0;
      for (let i = 0; i < freqData.length; i++) sum += freqData[i];
      const avg = sum / freqData.length;
      dbVal = Math.round(-48 + (avg / 255) * 44);

      for (let i = 0; i < numBars; i++) {
        const val = freqData[i % freqData.length] / 255;
        const height = Math.max(3, val * 18);
        ctx.fillStyle = val > 0.6 ? "#ff2a55" : (val > 0.3 ? "#00f0ff" : "#00e599");
        ctx.fillRect(i * spacing, (canvas.height - height) / 2, barWidth, height);
      }
    } else {
      for (let i = 0; i < numBars; i++) {
        let height = 3;
        if (audioActive) {
          height = 3 + Math.sin(Date.now() * 0.015 + i * 0.4) * 7 + Math.random() * 6;
          dbVal = Math.round(-24 + Math.random() * 12);
        }
        ctx.fillStyle = audioActive ? "#00f0ff" : "#1a2234";
        ctx.fillRect(i * spacing, (canvas.height - height) / 2, barWidth, height);
      }
    }

    if (el.vuMeterText) el.vuMeterText.textContent = `${dbVal} dB`;
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
  el.auditGroundingBtn.addEventListener("click", auditLinkedEvidence);

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

  // Calculators & Rx Safety
  el.calcHeartBtn.addEventListener("click", runHeartScoreCalculation);
  el.calcWellsBtn.addEventListener("click", runWellsPECalculation);
  el.calcQsofaBtn.addEventListener("click", runQsofaCalculation);
  el.calcGcsBtn.addEventListener("click", runGcsCalculation);
  el.runRxCheckBtn.addEventListener("click", runRxSafetyCheck);

  // AVS & Printable Chart
  el.generateAvsBtn.addEventListener("click", generatePatientAVS);
  el.openPrintChartBtn.addEventListener("click", openPrintableChartModal);
  el.closeModalBtn.addEventListener("click", () => el.chartModalOverlay.classList.remove("active"));
  el.printModalBtn.addEventListener("click", () => window.print());

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

    appendChatBubble("agent", data.agent_reply, data.agent_speech_text);
    speakText(data.agent_speech_text);

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
  row.id = `turn-${state.dialogueHistory.length}`;

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
      <span>🔊 TTS Speech Synthesized</span>
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

  state.dialogueHistory.push({ role, content });
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
        heart_rate_bpm: state.heartRate,
        spo2_percent: 96,
        respiratory_rate: 22,
        temperature_c: 37.2
      },
      telemetry_findings: `Lead II Telemetry shows ${state.currentRhythm} with rate ${state.heartRate} bpm.`
    };

    const res = await fetch("/api/triage/soap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("SOAP synthesis failed: " + res.statusText);
    const note = await res.json();
    state.lastSoapNote = note;

    if (typeof marked !== "undefined") {
      el.soapRenderedContent.innerHTML = marked.parse(note.markdown_formatted);
    } else {
      el.soapRenderedContent.innerText = note.markdown_formatted;
    }

    // Automatically trigger grounding audit
    auditLinkedEvidence();

  } catch (err) {
    console.error("SOAP note error:", err);
    alert("Error generating SOAP note: " + err.message);
  }
}


// --- LINKED EVIDENCE AUDIT (ABRIDGE ARCHITECTURE) ---
async function auditLinkedEvidence() {
  if (!state.lastSoapNote) {
    await generateSOAPNote();
    if (!state.lastSoapNote) return;
  }

  try {
    const res = await fetch("/api/triage/grounding", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        encounter_id: state.encounterId,
        soap_note: state.lastSoapNote
      })
    });

    if (!res.ok) throw new Error("Grounding audit failed");
    const data = await res.json();

    el.evidenceScoreBadge.textContent = `INTEGRITY ${data.grounding_integrity_percentage}%`;
    el.evidenceScoreBadge.className = `calc-badge ${data.hallucination_risk_level === 'ZERO_DETECTED' ? 'risk-low' : 'risk-mod'}`;

    el.evidenceListContainer.innerHTML = "";
    data.anchors.forEach(a => {
      const item = document.createElement("div");
      item.style.background = "var(--bg-card)";
      item.style.padding = "8px 10px";
      item.style.borderRadius = "4px";
      item.style.border = "1px solid var(--border-subtle)";
      item.innerHTML = `
        <div style="display: flex; justify-content: space-between; font-weight: 700; color: #fff; margin-bottom: 2px;">
          <span style="color: var(--neon-cyan); font-family: var(--font-mono);">[${a.target_section}]</span>
          <span style="font-size: 10px; color: var(--neon-green); font-family: var(--font-mono);">Score: ${Math.round(a.confidence_score * 100)}%</span>
        </div>
        <div style="font-size: 11px; color: #e2e8f0; margin-bottom: 4px;">${a.clinical_claim}</div>
        <div style="font-size: 11px; color: var(--text-dim); font-style: italic; border-left: 2px solid var(--neon-cyan); padding-left: 6px;">
          "${a.verbatim_transcript_quote}"
        </div>
      `;
      el.evidenceListContainer.appendChild(item);
    });

  } catch (err) {
    console.error("Grounding audit error:", err);
  }
}


// --- CLINICAL CALCULATORS (HEART, Wells, qSOFA, GCS) ---
async function runHeartScoreCalculation() {
  try {
    const payload = {
      history_suspicion: parseInt(document.getElementById("heartHistory").value, 10),
      ecg_finding: parseInt(document.getElementById("heartECG").value, 10),
      age: parseInt(document.getElementById("heartAge").value, 10) || 62,
      risk_factors: parseInt(document.getElementById("heartRisk").value, 10),
      troponin_initial: parseInt(document.getElementById("heartTrop").value, 10)
    };

    const res = await fetch("/api/calculators/heart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("heartScoreBadge").textContent = `Score: ${data.total_score} / 10`;
    const tag = document.getElementById("heartRiskTag");
    tag.textContent = `${data.risk_category} (${data.total_score} pts)`;
    tag.className = `calc-risk-tag ${data.total_score >= 7 ? 'risk-high' : (data.total_score >= 4 ? 'risk-mod' : 'risk-low')}`;
    document.getElementById("heartExpText").textContent = `${data.mace_six_week_rate}. ${data.recommended_pathway}`;

  } catch (err) {
    console.error("HEART calc error:", err);
  }
}

async function runWellsPECalculation() {
  try {
    const payload = {
      clinical_signs_dvt: document.getElementById("wellsDVT").checked,
      pe_most_likely_diagnosis: document.getElementById("wellsPEAlt").checked,
      heart_rate_over_100: document.getElementById("wellsHR").checked,
      immobilization_or_surgery_4w: document.getElementById("wellsImmob").checked,
      previous_dvt_or_pe: document.getElementById("wellsPrior").checked,
      hemoptysis: document.getElementById("wellsHemo").checked,
      active_malignancy: document.getElementById("wellsMalign").checked
    };

    const res = await fetch("/api/calculators/wells-pe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("wellsScoreBadge").textContent = `Score: ${data.total_score}`;
    const tag = document.getElementById("wellsRiskTag");
    tag.textContent = `${data.pe_probability_two_tier} (${data.total_score} pts)`;
    tag.className = `calc-risk-tag ${data.total_score > 4.0 ? 'risk-high' : 'risk-low'}`;
    document.getElementById("wellsExpText").textContent = `${data.pe_probability_three_tier}. ${data.recommended_workup}`;

  } catch (err) {
    console.error("Wells calc error:", err);
  }
}

async function runQsofaCalculation() {
  try {
    const payload = {
      respiratory_rate: parseInt(document.getElementById("qsofaRR").value, 10) || 22,
      systolic_bp: parseInt(document.getElementById("qsofaSBP").value, 10) || 95,
      altered_mentation: document.getElementById("qsofaGCS").checked
    };

    const res = await fetch("/api/calculators/qsofa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("qsofaBadge").textContent = `Score: ${data.score} / 3`;
    const tag = document.getElementById("qsofaRiskTag");
    tag.textContent = `${data.sepsis_risk_category} (${data.score}/3)`;
    tag.className = `calc-risk-tag ${data.score >= 2 ? 'risk-high' : 'risk-low'}`;
    document.getElementById("qsofaExpText").textContent = `${data.in_hospital_mortality_alert} ${data.recommended_management}`;

  } catch (err) {
    console.error("qSOFA calc error:", err);
  }
}

async function runGcsCalculation() {
  try {
    const payload = {
      eye_opening: parseInt(document.getElementById("gcsEye").value, 10),
      verbal_response: parseInt(document.getElementById("gcsVerbal").value, 10),
      motor_response: parseInt(document.getElementById("gcsMotor").value, 10)
    };

    const res = await fetch("/api/calculators/gcs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("gcsBadge").textContent = `Score: ${data.total_score} / 15`;
    const tag = document.getElementById("gcsRiskTag");
    tag.textContent = `${data.tbi_severity} (${data.total_score}/15)`;
    tag.className = `calc-risk-tag ${data.total_score <= 8 ? 'risk-high' : (data.total_score <= 12 ? 'risk-mod' : 'risk-low')}`;
    document.getElementById("gcsExpText").textContent = `${data.clinical_risk} ${data.airway_compromise_risk ? '⚠️ High risk of acute airway compromise; intubation precautions indicated.' : ''}`;

  } catch (err) {
    console.error("GCS calc error:", err);
  }
}

// --- RX SAFETY CHECKER ---
async function runRxSafetyCheck() {
  try {
    const allergies = el.rxAllergiesInput.value.split(",").map(s => s.trim()).filter(Boolean);
    const proposed = el.rxProposedInput.value.split(",").map(s => s.trim()).filter(Boolean);

    const res = await fetch("/api/safety/rx-check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_allergies: allergies,
        current_medications: state.patientProfile.current_medications,
        proposed_medications: proposed
      })
    });
    if (!res.ok) return;
    const data = await res.json();

    el.rxAlertsList.innerHTML = "";
    if (data.alerts.length === 0) {
      el.rxAlertsList.innerHTML = `
        <div style="background: rgba(0, 229, 153, 0.1); border: 1px solid var(--neon-green); color: var(--neon-green); padding: 10px 14px; border-radius: 6px; font-size: 12px;">
          ✓ All proposed medications cleared. No contraindications or cross-reactivity detected.
        </div>
      `;
      return;
    }

    data.alerts.forEach(a => {
      const card = document.createElement("div");
      card.className = `rx-alert-card rx-alert-${a.severity}`;
      card.innerHTML = `
        <div class="rx-alert-header">
          <span style="color: ${a.severity === 'CRITICAL_AVOID' ? 'var(--neon-red)' : 'var(--neon-amber)'};">
            ${a.severity === 'CRITICAL_AVOID' ? '🚨 CRITICAL CONTRAINDICATION' : '⚠️ CROSS-REACTIVITY / INTERACTION'} — ${a.trigger_drug.toUpperCase()}
          </span>
          <span style="font-size: 11px; opacity: 0.8;">${a.alert_type}</span>
        </div>
        <div style="color: #fff;"><strong>Trigger:</strong> ${a.offending_factor}</div>
        <div style="color: #cbd5e1; font-size: 11px;">${a.clinical_mechanism}</div>
        <div style="color: var(--neon-green); font-size: 11px; margin-top: 2px;">
          <strong>Safe Alternative:</strong> ${a.recommended_safe_alternative}
        </div>
      `;
      el.rxAlertsList.appendChild(card);
    });

  } catch (err) {
    console.error("Rx check error:", err);
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


// --- PATIENT AFTER-VISIT SUMMARY (AVS) ---
async function generatePatientAVS() {
  if (!state.latestAssessment) {
    alert("Conduct triage intake first.");
    return;
  }

  try {
    const res = await fetch("/api/triage/avs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        encounter_id: state.encounterId,
        patient_profile: state.patientProfile,
        assessment: state.latestAssessment,
        soap_note: state.lastSoapNote
      })
    });

    if (!res.ok) throw new Error("AVS failed");
    const avs = await res.json();
    state.lastAvs = avs;

    if (typeof marked !== "undefined") {
      el.avsRenderedContent.innerHTML = marked.parse(avs.formatted_document_markdown);
    } else {
      el.avsRenderedContent.innerText = avs.formatted_document_markdown;
    }

  } catch (err) {
    console.error("AVS generation error:", err);
  }
}

function openPrintableChartModal() {
  if (!state.latestAssessment) {
    alert("Please conduct a clinical intake or load a scenario first.");
    return;
  }

  const p = state.patientProfile;
  const a = state.latestAssessment;
  const note = state.lastSoapNote;

  el.printableChartBody.innerHTML = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.5; padding: 20px;">
      <div style="border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
          <h1 style="font-size: 22px; margin: 0 0 4px 0; letter-spacing: -0.5px;">VAANI CLINICAL HEALTH SYSTEM</h1>
          <div style="font-size: 13px; color: #555;">EMERGENCY TELEMEDICINE & CLINICAL TELEPHONY TRIAGE SERVICE</div>
        </div>
        <div style="text-align: right; font-size: 12px; font-family: monospace;">
          <strong>ENCOUNTER ID:</strong> ${state.encounterId}<br>
          <strong>DATE/TIME:</strong> ${new Date().toUTCString()}
        </div>
      </div>

      <div style="background: #f4f6f8; border: 1px solid #ddd; padding: 12px; border-radius: 4px; margin-bottom: 16px; display: grid; grid-template-columns: 2fr 1fr 1fr;">
        <div><strong>Patient Name:</strong> ${p.name} | <strong>MRN:</strong> ${p.mrn}</div>
        <div><strong>Age / Sex:</strong> ${p.age || 'Unspecified'} / ${p.biological_sex.toUpperCase()}</div>
        <div><strong>Triage Rating:</strong> <span style="background: #000; color: #fff; padding: 2px 6px; font-size: 11px; font-weight: bold;">${a.triage_status}</span></div>
      </div>

      <div style="margin-bottom: 14px;">
        <h3 style="font-size: 15px; margin: 0 0 6px 0; border-bottom: 1px solid #ccc; padding-bottom: 2px;">HISTORY OF PRESENT ILLNESS (OLD CARTS)</h3>
        <p style="font-size: 13px; margin: 0 0 6px 0;"><strong>Chief Complaint:</strong> ${a.chief_complaint}</p>
        <p style="font-size: 13px; margin: 0 0 6px 0;">
          Onset: ${a.hpi.onset || 'Unspecified'} | Location: ${a.hpi.location || 'Unspecified'} | Duration: ${a.hpi.duration || 'Unspecified'}<br>
          Character: ${a.hpi.character || 'Unspecified'} | Radiation: ${a.hpi.radiation || 'None'} | Pain Score: ${a.hpi.severity || '--'}/10
        </p>
      </div>

      <div style="margin-bottom: 14px;">
        <h3 style="font-size: 15px; margin: 0 0 6px 0; border-bottom: 1px solid #ccc; padding-bottom: 2px;">DIAGNOSTIC ASSESSMENT & ICD-10-CM</h3>
        <p style="font-size: 13px; margin: 0 0 6px 0;">
          <strong>Primary Working Diagnosis:</strong> ${a.differentials[0] ? a.differentials[0].condition_name : 'Acute Symptom Complex'} 
          (ICD-10: <code>${a.differentials[0] ? a.differentials[0].icd10_code : 'R69'}</code>)
        </p>
      </div>

      <div style="margin-bottom: 14px;">
        <h3 style="font-size: 15px; margin: 0 0 6px 0; border-bottom: 1px solid #ccc; padding-bottom: 2px;">RECOMMENDED PLAN & DISPOSITION</h3>
        <p style="font-size: 13px; margin: 0 0 6px 0;"><strong>Disposition:</strong> ${a.recommended_disposition}</p>
      </div>

      <div style="border-top: 1px dashed #999; padding-top: 10px; font-size: 11px; color: #666; display: flex; justify-content: space-between;">
        <span>Document Electronically Signed via Vaani Clinical CDS Engine</span>
        <span>HL7 FHIR Release 4 Compliant</span>
      </div>
    </div>
  `;

  el.chartModalOverlay.classList.add("active");
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
  state.encounterId = "ENC-" + Math.floor(10000 + Math.random() * 90000);
  state.patientProfile = sc.patient_profile;
  state.dialogueHistory = [];
  updatePatientHUD();

  // If scenario is cardiac or asthma, update rhythm
  if (sc.id === "scenario-stemi-cardiac") {
    document.querySelector('[data-rhythm="STEMI"]').click();
  } else if (sc.id === "scenario-asthma-bronchospasm") {
    document.querySelector('[data-rhythm="TACHY"]').click();
  } else if (sc.id === "scenario-stroke-fast") {
    document.querySelector('[data-rhythm="NSR"]').click();
  }

  el.dialogueStream.innerHTML = `
    <div class="msg-row agent">
      <div class="msg-meta">VAANI CLINICAL AI RECEPTIONIST • INTAKE</div>
      <div class="msg-bubble">
        Hello, this is the Vaani Clinical Triage Service. I am an intelligent clinical receptionist. 
        Please describe what symptoms or medical emergency you are experiencing today.
      </div>
    </div>
  `;

  document.querySelector('[data-target="workspace-triage"]').click();

  for (const msg of sc.sample_dialogue) {
    await sendPatientMessage(msg.content);
    await new Promise(r => setTimeout(r, 600));
  }

  if (sc.lab_text_snippet) {
    el.labInputText.value = sc.lab_text_snippet;
    await extractBiomarkersFromText(sc.lab_text_snippet);
  }

  setTimeout(async () => {
    await generateSOAPNote();
    await generatePatientAVS();
    await compileFHIRBundle();
  }, 800);
}
