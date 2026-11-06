/**
 * Vaani Clinical (वाणी) — Enterprise Clinical Intelligence Workstation
 * Inspired by Sehatlings Muaina & High-End Clinical Telehealth Suites
 * Incorporates Daktari AI Telephony, ScanUp Pathology Gauges, One-Tap-Go Triage,
 * Abridge Linked Evidence Grounding, and HL7 FHIR Release 4 Interoperability.
 */

async function apiFetch(url, options) {
  try {
    const response = await window.fetch(url, options);
    if (!response.ok) throw new Error(`Request failed (${response.status}). Review the input and try again.`);
    return response;
  } catch (error) {
    showNotice(error.message || "Connection unavailable. Please try again.");
    throw error;
  }
}

// Application State
const state = {
  encounterId: "ENC-" + crypto.randomUUID(),
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
  ttsActive: false,
  sendingEncounter: null,
  extractingEncounter: null,
  revision: 0,
  lastSoapNote: null,
  lastFhirBundle: null,
  lastAvs: null,
  // ICU Telemetry & Arrhythmia simulation
  currentRhythm: "TACHY",
  heartRate: 118,
  // Web Audio & Speech recognition
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
  // ScanUp Pathology Gauges
  labInputText: document.getElementById("labInputText"),
  pasteSampleLabBtn: document.getElementById("pasteSampleLabBtn"),
  extractLabBtn: document.getElementById("extractLabBtn"),
  biomarkerGaugesGrid: document.getElementById("biomarkerGaugesGrid"),
  bioOrganAlertCount: document.getElementById("bioOrganAlertCount"),
  // Calculators & Rx Safety
  calcHeartBtn: document.getElementById("calcHeartBtn"),
  calcWellsBtn: document.getElementById("calcWellsBtn"),
  runRxCheckBtn: document.getElementById("runRxCheckBtn"),
  rxAllergiesInput: document.getElementById("rxAllergiesInput"),
  rxProposedInput: document.getElementById("rxProposedInput"),
  rxAlertsList: document.getElementById("rxAlertsList"),
  // EHR Scribe & Grounding
  generateSoapBtn: document.getElementById("generateSoapBtn"),
  generateAvsBtn: document.getElementById("generateAvsBtn"),
  openPrintChartBtn: document.getElementById("openPrintChartBtn"),
  copySoapBtn: document.getElementById("copySoapBtn"),
  soapRenderedContent: document.getElementById("soapRenderedContent"),
  evidenceListContainer: document.getElementById("evidenceListContainer"),
  evidenceScoreBadge: document.getElementById("evidenceScoreBadge"),
  downloadFhirBtn: document.getElementById("downloadFhirBtn"),
  fhirCodeView: document.getElementById("fhirCodeView"),
  // Modals
  chartModalOverlay: document.getElementById("chartModalOverlay"),
  closeModalBtn: document.getElementById("closeModalBtn"),
  printModalBtn: document.getElementById("printModalBtn"),
  printableChartBody: document.getElementById("printableChartBody"),
  dtmfModalOverlay: document.getElementById("dtmfModalOverlay"),
  closeDtmfBtn: document.getElementById("closeDtmfBtn"),
  dtmfNumberDisplay: document.getElementById("dtmfNumberDisplay"),
  // Scenarios
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

  // Run initial calculations
  runHeartScoreCalculation();
  runWellsPECalculation();
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
  const tabs = document.querySelectorAll(".suite-tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-target");
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".suite-panel").forEach(p => p.classList.remove("active"));

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
  if (el.currentEncounterId) el.currentEncounterId.title = state.encounterId;
  window.refreshEncounterUI?.();
}


// --- ARRHYTHMIA & ECG CARDIAC WAVEFORM MONITOR ---
function initECGMonitor() {
  const canvas = el.ecgCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resizeCanvas() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = 52;
  }
  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);

  let x = 0;
  let prevY = canvas.height / 2;
  let cycle = 0;
  let afibNoisePhase = 0;

  // Rhythm selector event buttons
  document.querySelectorAll(".rhythm-pill").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".rhythm-pill").forEach(b => b.classList.remove("active"));
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
      // Coarse Ventricular Fibrillation: chaotic sinusoidal arrest oscillation
      return baseline + Math.sin(t * 0.12) * 14 + Math.sin(t * 0.28) * 8 + (Math.random() - 0.5) * 6;
    }

    const normT = (t % 100) / 100; // 0.0 to 1.0

    if (rhythm === "STEMI") {
      // Marked ST segment elevation (tombstone pattern)
      if (normT > 0.15 && normT < 0.22) {
        return baseline - Math.sin((normT - 0.15) / 0.07 * Math.PI) * 4;
      } else if (normT >= 0.28 && normT < 0.30) {
        return baseline + 3;
      } else if (normT >= 0.30 && normT < 0.34) {
        return baseline - 24;
      } else if (normT >= 0.34 && normT < 0.37) {
        return baseline - 8;
      } else if (normT >= 0.37 && normT < 0.65) {
        return baseline - 12 - Math.sin((normT - 0.37) / 0.28 * Math.PI) * 7;
      }
      return baseline;
    }

    if (rhythm === "AFIB") {
      // Atrial Fibrillation: No P waves, irregular baseline, random R intervals
      afibNoisePhase += 0.2;
      const fWaveNoise = Math.sin(afibNoisePhase * 3.4) * 2.2 + (Math.random() - 0.5) * 2.5;
      if (normT >= 0.30 && normT < 0.34) {
        return baseline - 22;
      } else if (normT >= 0.34 && normT < 0.37) {
        return baseline + 6;
      } else if (normT > 0.48 && normT < 0.62) {
        return baseline - Math.sin((normT - 0.48) / 0.14 * Math.PI) * 4 + fWaveNoise;
      }
      return baseline + fWaveNoise;
    }

    // Normal Sinus (NSR) & Sinus Tachycardia (TACHY)
    if (normT > 0.15 && normT < 0.22) {
      return baseline - Math.sin((normT - 0.15) / 0.07 * Math.PI) * 4;
    } else if (normT >= 0.28 && normT < 0.30) {
      return baseline + 3;
    } else if (normT >= 0.30 && normT < 0.34) {
      return baseline - 24;
    } else if (normT >= 0.34 && normT < 0.37) {
      return baseline + 7;
    } else if (normT > 0.48 && normT < 0.62) {
      return baseline - Math.sin((normT - 0.48) / 0.14 * Math.PI) * 6;
    }

    return baseline + (Math.random() - 0.5) * 1.0;
  }

  function drawECG() {
    ctx.fillStyle = "rgba(2, 4, 9, 0.09)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Subtle grid lines
    ctx.strokeStyle = "rgba(20, 32, 56, 0.4)";
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    for (let gy = 0; gy < canvas.height; gy += 13) {
      ctx.moveTo(0, gy);
      ctx.lineTo(canvas.width, gy);
    }
    ctx.stroke();

    const speed = 2.4;
    const y = getEcgY(cycle, state.currentRhythm);

    const isArrest = state.currentRhythm === "VFIB";
    ctx.shadowBlur = isArrest ? 12 : 8;
    ctx.shadowColor = isArrest ? "#f43f5e" : "#10b981";
    ctx.strokeStyle = isArrest ? "#fb7185" : "#34d399";
    ctx.lineWidth = 1.9;

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
  document.querySelectorAll(".dtmf-key").forEach(btn => {
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
    el.liveMicBtn.classList.add("active-pulse");
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
  state.analyserNode = null;
  el.liveMicBtn.classList.remove("active-pulse");
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
    if (!state.isLiveMicActive) {
      stream.getTracks().forEach(track => track.stop());
      return;
    }
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
    canvas.width = Math.max(1, canvas.parentElement.clientWidth - 160);
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
        ctx.fillStyle = val > 0.6 ? "#f43f5e" : (val > 0.3 ? "#00e5ff" : "#10b981");
        ctx.fillRect(i * spacing, (canvas.height - height) / 2, barWidth, height);
      }
    } else {
      for (let i = 0; i < numBars; i++) {
        let height = 3;
        if (audioActive) {
          height = 3 + Math.sin(Date.now() * 0.015 + i * 0.4) * 7 + Math.random() * 6;
          dbVal = Math.round(-24 + Math.random() * 12);
        }
        ctx.fillStyle = audioActive ? "#00e5ff" : "#1a2234";
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
      el.ttsStatus.textContent = "Audio on";
    } else {
      window.speechSynthesis?.cancel();
      el.ttsIcon.textContent = "🔇";
      el.ttsStatus.textContent = "Audio off";
    }
  });

  // Chat form submit
  el.chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = el.patientInput.value.trim();
    if (!text) return;
    if (state.sendingEncounter === state.encounterId || state.extractingEncounter === state.encounterId) { showNotice("Please wait for the current update to finish. Your message is still here."); return; }
    el.patientInput.value = "";
    sendPatientMessage(text);
  });

  // Reset call button
  el.resetCallBtn.addEventListener("click", () => {
    resetEncounter();

    el.dialogueStream.innerHTML = `
      <div class="message-bubble-row agent">
        <div class="bubble-meta">Vaani · Intake assistant • INTAKE</div>
        <div class="bubble-text">
          Welcome to Vaani. This is a simulated clinical intake.
          Please describe what symptoms or medical emergency you are experiencing today.
        </div>
      </div>
    `;
    resetTriageHUD();
  });

  // Escalate 911 button
  el.escalate911Btn.addEventListener("click", () => {
    showNotice("Simulation only. No call has been placed and no ambulance has been dispatched. In a real emergency, contact your local emergency service directly.");
  });

  // SOAP Studio buttons
  el.generateSoapBtn.addEventListener("click", generateSOAPNote);
  el.copySoapBtn.addEventListener("click", () => {
    if (state.lastSoapNote && state.lastSoapNote.markdown_formatted) {
      navigator.clipboard.writeText(state.lastSoapNote.markdown_formatted).then(() => {
        showNotice("SOAP Note Markdown copied to clipboard!");
      }).catch(() => showNotice("Clipboard unavailable. Select and copy the note manually."));
    } else {
      showNotice("Please synthesize a SOAP note first.");
    }
  });

  // ScanUp Pathology Lab buttons
  el.pasteSampleLabBtn.addEventListener("click", () => {
    el.labInputText.value =
`Comprehensive Clinical Lab Panel:
Cardiac Troponin I: 1.45 ng/mL
BNP: 420 pg/mL
D-Dimer: 0.38 ug/mL FEU
Serum Fasting Glucose: 285 mg/dL
HbA1c: 9.8 %
Serum Creatinine: 2.4 mg/dL
eGFR: 42 mL/min/1.73m2
Serum Potassium: 5.6 mEq/L
Blood Hemoglobin: 13.8 g/dL
White Blood Cell: 12.8 x10^3/uL`;
  });

  el.extractLabBtn.addEventListener("click", () => {
    const raw = el.labInputText.value.trim();
    if (!raw) {
      showNotice("Please enter or paste clinical lab text.");
      return;
    }
    extractBiomarkersFromText(raw);
  });

  // Calculators & Rx Safety
  el.calcHeartBtn.addEventListener("click", runHeartScoreCalculation);
  el.calcWellsBtn.addEventListener("click", runWellsPECalculation);
  el.runRxCheckBtn.addEventListener("click", runRxSafetyCheck);

  // AVS & Printable Chart
  el.generateAvsBtn.addEventListener("click", generatePatientAVS);
  el.openPrintChartBtn.addEventListener("click", openPrintableChartModal);
  el.closeModalBtn.addEventListener("click", () => el.chartModalOverlay.classList.remove("active"));
  el.printModalBtn.addEventListener("click", () => window.print());

  // FHIR Explorer buttons
  el.downloadFhirBtn.addEventListener("click", () => {
    if (!state.lastFhirBundle) {
      showNotice("Compile FHIR bundle first.");
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



// Treat generated clinical content as text, including in formatted reports.
function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function renderMarkdown(text) {
  return escapeHTML(text).split("\n").map(line => {
    const heading = line.match(/^(#{1,4}) (.*)$/);
    const body = (heading ? heading[2] : line).replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    return heading ? `<h${heading[1].length}>${body}</h${heading[1].length}>` : `<p>${body || "&nbsp;"}</p>`;
  }).join("");
}
function clearGeneratedRecords() {
  state.lastSoapNote = null;
  state.lastFhirBundle = null;
  state.lastAvs = null;
  el.soapRenderedContent.textContent = "Your encounter note will appear here after an intake.";
  el.fhirCodeView.textContent = "No export generated for this encounter.";
  el.evidenceListContainer.textContent = "Generate a note to review transcript evidence.";
  el.evidenceScoreBadge.textContent = "Not audited";
  el.printableChartBody.replaceChildren();
  el.chartModalOverlay.classList.remove("active");
  window.refreshEncounterUI?.();
}
function resetEncounter(profile = state.patientProfile) {
  state.encounterId = "ENC-" + crypto.randomUUID();
  state.revision += 1;
  state.patientProfile = profile;
  state.dialogueHistory = [];
  state.currentHPI = {};
  state.latestAssessment = null;
  state.extractedBiomarkers = [];
  state.sendingEncounter = null;
  state.extractingEncounter = null;
  el.extractLabBtn.disabled = false;
  window.speechSynthesis?.cancel();
  state.speechRecognizer?.abort();
  stopLiveMic();
  clearGeneratedRecords();
  el.labInputText.value = "";
  el.bioOrganAlertCount.textContent = "No results";
  el.rxAlertsList.textContent = "Run a medication check for this encounter.";
  renderScanUpGauges([]);
  resetTriageHUD();
  updatePatientHUD();
  const sendButton = el.chatForm.querySelector('button[type="submit"]');
  if (sendButton) sendButton.disabled = false;
}

// --- SEND PATIENT MESSAGE TO BACKEND API ---
async function sendPatientMessage(text) {
  const encounterId = state.encounterId;
  if (state.sendingEncounter === encounterId || state.extractingEncounter === encounterId) { showNotice("Please wait for the current encounter update to finish."); return false; }
  state.sendingEncounter = encounterId;
  state.revision += 1;
  clearGeneratedRecords();
  const sendButton = el.chatForm.querySelector('button[type="submit"]');
  if (sendButton) sendButton.disabled = true;
  appendChatBubble("patient", text);
  window.refreshEncounterUI?.();
  pulseAudioVis(1200);

  try {
    const response = await apiFetch("/api/triage/message", {
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
    if (state.encounterId !== encounterId) return false;

    appendChatBubble("agent", data.agent_reply, data.agent_speech_text);
    speakText(data.agent_speech_text);

    state.latestAssessment = data.triage_assessment;
    state.currentHPI = data.triage_assessment.hpi;
    if (data.extracted_biomarkers) state.extractedBiomarkers = data.extracted_biomarkers;

    updateTriageHUD(data);
    return true;

  } catch (err) {
    console.error("Triage message failed:", err);
    if (state.encounterId === encounterId) appendChatBubble("agent", "Could not complete this intake. Please check the connection and try again.");
    return false;
  } finally {
    if (state.sendingEncounter === encounterId) {
      state.sendingEncounter = null;
      if (sendButton) sendButton.disabled = false;
      window.refreshEncounterUI?.();
    }
  }
}


// --- CHAT STREAM BUBBLE BUILDER ---
function appendChatBubble(role, content, speechText = null) {
  const row = document.createElement("div");
  row.className = `message-bubble-row ${role}`;
  row.id = `turn-${state.dialogueHistory.length}`;

  const meta = document.createElement("div");
  meta.className = "bubble-meta";
  meta.textContent = role === "patient"
    ? `${state.patientProfile.name.toUpperCase()} (CALLER)`
    : "Vaani · Intake assistant";

  const bubble = document.createElement("div");
  bubble.className = "bubble-text";
  bubble.textContent = content;
  bubble.style.whiteSpace = "pre-wrap";

  if (speechText) {
    const audioBar = document.createElement("div");
    audioBar.className = "bubble-tts-bar";
    audioBar.innerHTML = `
      <span>🔊 TTS Speech Synthesized</span>
      <button class="btn-revoice">PLAY AGAIN</button>
    `;
    audioBar.querySelector(".btn-revoice").addEventListener("click", () => {
      speakText(speechText);
    });
    bubble.appendChild(audioBar);
  }

  row.appendChild(meta);
  row.appendChild(bubble);
  el.dialogueStream.appendChild(row);
  el.dialogueStream.scrollTop = el.dialogueStream.scrollHeight;

  state.dialogueHistory.push({ role, content });
  window.refreshEncounterUI?.();
}


// --- UPDATE TRIAGE HUD WITH ASSESSMENT ---
function updateTriageHUD(data) {
  const assess = data.triage_assessment;
  const hpi = assess.hpi;

  // ESI Badge
  el.esiBadgeDisplay.className = `esi-tag esi-${assess.esi_level}`;
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

  // Differentials with Bayesian Probability Progress Bars
  el.diffListContainer.innerHTML = "";
  if (assess.differentials && assess.differentials.length > 0) {
    assess.differentials.forEach(diff => {
      const probPct = diff.probability_percentage || (diff.probability === 'High' ? 88 : (diff.probability === 'Moderate' ? 10 : 2));
      const isHigh = probPct > 50;

      const card = document.createElement("div");
      card.className = "diff-card";
      card.innerHTML = `
        <div class="diff-card-head">
          <span>${escapeHTML(diff.condition_name)}</span>
          <span class="diff-icd-chip">${escapeHTML(diff.icd10_code)}</span>
        </div>
        <div class="diff-prob-track">
          <div class="diff-prob-fill ${isHigh ? 'high' : ''}" style="width: ${probPct}%;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 11px; font-family: var(--font-code);">
          <span style="color: ${isHigh ? 'var(--clinical-rose)' : 'var(--clinical-cyan)'}; font-weight: 700;">${probPct}% Probability</span>
          <span style="color: var(--text-dim);">${escapeHTML(diff.organ_system || 'General')}</span>
        </div>
        <div class="diff-meta-desc">${escapeHTML(diff.justification)}</div>
      `;
      el.diffListContainer.appendChild(card);
    });
  }

  if (data.extracted_biomarkers && data.extracted_biomarkers.length > 0) {
    renderScanUpGauges(data.extracted_biomarkers);
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
  el.esiBadgeDisplay.className = "esi-tag esi-3";
  el.esiBadgeDisplay.textContent = "Awaiting intake";
  el.esiDispositionText.textContent = "Awaiting clinical symptom assessment and OLD CARTS parameters.";
  el.triagePhaseBadge.textContent = "INTAKE";
  el.emergencyBanner.classList.add("hidden");

  ["Onset", "Location", "Duration", "Character", "Aggravating", "Relieving", "Radiation"].forEach(key => {
    setOldcartVal(el[`oldcart${key}`], null);
  });
  el.oldcartSeverity.textContent = "-- / 10";
  el.oldcartSeverity.classList.add("empty");

  el.diffListContainer.innerHTML = `
    <div class="diff-card">
      <div class="diff-card-head">
        <span>Awaiting symptom report</span>
        <span class="diff-icd-chip">Z00.00</span>
      </div>
      <div class="diff-meta-desc">Possible conditions will appear after an intake. Scores are illustrative.</div>
    </div>
  `;
}


// --- SCANUP VISUAL PATHOLOGY GAUGES (Inspired by Sehatlings Muaina) ---
async function extractBiomarkersFromText(clinicalText) {
  if (state.sendingEncounter === state.encounterId || state.extractingEncounter === state.encounterId) { showNotice("Finish the current update before reviewing another panel."); return; }
  state.extractingEncounter = state.encounterId;
  el.extractLabBtn.disabled = true;
  state.revision += 1;
  clearGeneratedRecords();
  const requestEncounter = state.encounterId;
  const requestRevision = state.revision;
  window.refreshEncounterUI?.();
  try {
    const res = await apiFetch("/api/triage/biomarkers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        encounter_id: state.encounterId,
        clinical_text: clinicalText
      })
    });

    if (!res.ok) throw new Error("Biomarker extraction failed");
    const data = await res.json();
    if (state.encounterId !== requestEncounter || state.revision !== requestRevision) return;

    const latest = new Map(state.extractedBiomarkers.map(item => [item.test_code, item]));
    data.biomarkers.forEach(item => latest.set(item.test_code, item));
    state.extractedBiomarkers = [...latest.values()];
    renderScanUpGauges(state.extractedBiomarkers);

  } catch (err) {
    console.error("ScanUp lab error:", err);
    if (state.encounterId === requestEncounter) showNotice("Biomarker extraction error: " + err.message);
  } finally {
    if (state.extractingEncounter === requestEncounter) {
      state.extractingEncounter = null;
      el.extractLabBtn.disabled = false;
      window.refreshEncounterUI?.();
    }
  }
}

function renderScanUpGauges(biomarkers) {
  if (!el.biomarkerGaugesGrid) return;
  const critical = (biomarkers || []).filter(item => item.status.startsWith("CRITICALLY_")).length;
  el.bioOrganAlertCount.textContent = biomarkers?.length ? `${critical} critical result${critical === 1 ? "" : "s"}` : "No results";
  el.bioOrganAlertCount.style.color = critical > 0 ? "var(--clinical-rose)" : "var(--clinical-emerald)";
  if (!biomarkers || biomarkers.length === 0) {
    el.biomarkerGaugesGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; color: var(--text-dim); padding: 48px;">
        No biomarkers parsed yet.
      </div>
    `;
    return;
  }

  el.biomarkerGaugesGrid.innerHTML = "";
  biomarkers.forEach(b => {
    // Calculate gauge pointer position: 0% to 100%
    const maxVal = b.reference_high * 2.0;
    const pct = Math.min(94, Math.max(6, (b.value / (maxVal || 1.0)) * 100));

    const card = document.createElement("div");
    card.className = "bio-gauge-card";
    card.innerHTML = `
      <div class="bio-card-top">
        <span class="bio-test-title">${escapeHTML(b.name)} (${escapeHTML(b.test_code)})</span>
        <span class="bio-loinc-badge">LOINC: ${escapeHTML(b.loinc_code)}</span>
      </div>
      <div class="bio-value-row">
        <span class="bio-measured-num">${b.value} <span style="font-size: 13px; color: var(--text-secondary); font-weight: normal;">${escapeHTML(b.unit)}</span></span>
        <span class="bio-status-pill status-${b.status}">${b.status}</span>
      </div>

      <!-- Visual Reference Interval Slider Track -->
      <div class="reference-slider-track">
        <div class="gauge-pointer-needle" style="left: ${pct}%;"></div>
      </div>
      <div class="reference-bounds-label">
        <span>Low: ${b.reference_low} ${escapeHTML(b.unit)}</span>
        <span>High: ${b.reference_high} ${escapeHTML(b.unit)}</span>
      </div>
      <div class="bio-interp-text">${escapeHTML(b.clinical_interpretation)}</div>
    `;
    el.biomarkerGaugesGrid.appendChild(card);
  });
}


// --- SOAP NOTE SYNTHESIS ---
async function generateSOAPNote() {
  if (state.sendingEncounter === state.encounterId || state.extractingEncounter === state.encounterId) { showNotice("Finish the current update before generating a document."); return; }
  const requestEncounter = state.encounterId;
  const requestRevision = state.revision;
  if (!state.latestAssessment) {
    showNotice("Please conduct a triage intake first so clinical parameters are present.");
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

    const res = await apiFetch("/api/triage/soap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("SOAP synthesis failed: " + res.statusText);
    const note = await res.json();
    if (state.encounterId !== requestEncounter || state.revision !== requestRevision) return;
    state.lastSoapNote = note;

    el.soapRenderedContent.innerHTML = renderMarkdown(note.markdown_formatted);

    await Promise.all([auditLinkedEvidence(), compileFHIRBundle()]);

  } catch (err) {
    console.error("SOAP note error:", err);
    showNotice("Error generating SOAP note: " + err.message);
  }
}


// --- LINKED EVIDENCE AUDIT (ABRIDGE ARCHITECTURE) ---
async function auditLinkedEvidence() {
  const requestEncounter = state.encounterId;
  const requestRevision = state.revision;
  if (!state.lastSoapNote) return;

  try {
    const res = await apiFetch("/api/triage/grounding", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        encounter_id: state.encounterId,
        soap_note: state.lastSoapNote
      })
    });

    if (!res.ok) throw new Error("Grounding audit failed");
    const data = await res.json();
    if (state.encounterId !== requestEncounter || state.revision !== requestRevision) return;

    el.evidenceScoreBadge.textContent = `INTEGRITY ${data.grounding_integrity_percentage}%`;

    el.evidenceListContainer.innerHTML = "";
    data.anchors.forEach(a => {
      const item = document.createElement("div");
      item.className = "evidence-card-item";
      item.innerHTML = `
        <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-primary);">
          <span style="color: var(--clinical-cyan); font-family: var(--font-code);">[${escapeHTML(a.target_section)}]</span>
          <span style="font-size: 11px; color: var(--clinical-emerald); font-family: var(--font-code);">${Math.round(a.confidence_score * 100)}% Match</span>
        </div>
        <div style="font-size: 12px; color: var(--text-secondary);">${escapeHTML(a.clinical_claim)}</div>
        <div style="font-size: 11px; color: var(--text-muted); font-style: italic; border-left: 2px solid var(--clinical-cyan); padding-left: 6px;">
          "${escapeHTML(a.verbatim_transcript_quote)}"
        </div>
      `;
      el.evidenceListContainer.appendChild(item);
    });

  } catch (err) {
    console.error("Grounding audit error:", err);
  }
}


// --- CLINICAL CALCULATORS (HEART & Wells PE) ---
async function runHeartScoreCalculation() {
  const requestEncounter = state.encounterId;
  const requestRevision = state.revision;
  try {
    const payload = {
      history_suspicion: parseInt(document.getElementById("heartHistory").value, 10),
      ecg_finding: parseInt(document.getElementById("heartECG").value, 10),
      age: parseInt(document.getElementById("heartAge").value, 10) || 62,
      risk_factors: parseInt(document.getElementById("heartRisk").value, 10),
      troponin_initial: parseInt(document.getElementById("heartTrop").value, 10)
    };

    const res = await apiFetch("/api/calculators/heart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) return;
    const data = await res.json();
    if (requestEncounter !== state.encounterId || requestRevision !== state.revision) return;

    document.getElementById("heartScoreBadge").textContent = `Score: ${data.total_score} / 10`;
    const tag = document.getElementById("heartRiskTag");
    tag.textContent = `${data.risk_category} (${data.total_score} pts)`;
    document.getElementById("heartExpText").textContent = `${data.mace_six_week_rate}. ${data.recommended_pathway}`;

  } catch (err) {
    console.error("HEART calc error:", err);
  }
}

async function runWellsPECalculation() {
  const requestEncounter = state.encounterId;
  const requestRevision = state.revision;
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

    const res = await apiFetch("/api/calculators/wells-pe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) return;
    const data = await res.json();
    if (requestEncounter !== state.encounterId || requestRevision !== state.revision) return;

    document.getElementById("wellsScoreBadge").textContent = `Score: ${data.total_score}`;
    const tag = document.getElementById("wellsRiskTag");
    tag.textContent = `${data.pe_probability_two_tier} (${data.total_score} pts)`;
    document.getElementById("wellsExpText").textContent = `${data.pe_probability_three_tier}. ${data.recommended_workup}`;

  } catch (err) {
    console.error("Wells calc error:", err);
  }
}


// --- RX SAFETY CHECKER ---
async function runRxSafetyCheck() {
  const requestEncounter = state.encounterId;
  const requestRevision = state.revision;
  try {
    const allergies = el.rxAllergiesInput.value.split(",").map(s => s.trim()).filter(Boolean);
    const proposed = el.rxProposedInput.value.split(",").map(s => s.trim()).filter(Boolean);

    const res = await apiFetch("/api/safety/rx-check", {
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
    if (requestEncounter !== state.encounterId || requestRevision !== state.revision) return;

    el.rxAlertsList.innerHTML = "";
    if (data.alerts.length === 0) {
      el.rxAlertsList.innerHTML = `
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--clinical-emerald); color: var(--clinical-emerald); padding: 10px 14px; border-radius: 6px; font-size: 13px;">
          ✓ All proposed medications cleared. No contraindications or cross-reactivity detected.
        </div>
      `;
      return;
    }

    data.alerts.forEach(a => {
      const card = document.createElement("div");
      card.className = `rx-alert-banner rx-alert-${a.severity}`;
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; font-weight: 700; font-family: var(--font-code);">
          <span style="color: ${a.severity === 'CRITICAL_AVOID' ? 'var(--clinical-rose)' : 'var(--clinical-amber)'};">
            ${a.severity === 'CRITICAL_AVOID' ? '🚨 CRITICAL CONTRAINDICATION' : '⚠️ CROSS-REACTIVITY / INTERACTION'} — ${escapeHTML(a.trigger_drug.toUpperCase())}
          </span>
          <span style="font-size: 11px; opacity: 0.8;">${a.alert_type}</span>
        </div>
        <div style="color: var(--text-primary);"><strong>Trigger:</strong> ${escapeHTML(a.offending_factor)}</div>
        <div style="color: var(--text-secondary); font-size: 12px;">${escapeHTML(a.clinical_mechanism)}</div>
        <div style="color: var(--clinical-emerald); font-size: 12px; margin-top: 2px;">
          <strong>Safe Alternative:</strong> ${escapeHTML(a.recommended_safe_alternative)}
        </div>
      `;
      el.rxAlertsList.appendChild(card);
    });

  } catch (err) {
    console.error("Rx check error:", err);
  }
}


// --- PATIENT AFTER-VISIT SUMMARY (AVS) ---
async function generatePatientAVS() {
  if (state.sendingEncounter === state.encounterId || state.extractingEncounter === state.encounterId) { showNotice("Finish the current update before generating a document."); return; }
  const requestEncounter = state.encounterId;
  const requestRevision = state.revision;
  if (!state.latestAssessment) {
    showNotice("Conduct triage intake first.");
    return;
  }

  try {
    const res = await apiFetch("/api/triage/avs", {
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
    if (state.encounterId !== requestEncounter || state.revision !== requestRevision) return;
    state.lastAvs = avs;

    // Render in modal preview
    el.printableChartBody.innerHTML = `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; padding: 20px;">
        <h2 style="font-size: 22px; color: #0284c7; margin-bottom: 12px;">Patient Care Summary & Home Instructions</h2>
        <div style="font-size: 14px; color: #334155; margin-bottom: 16px;">${escapeHTML(avs.what_happened_today)}</div>
        <h3 style="font-size: 16px; color: #dc2626; margin-top: 16px;">⚠️ Warning Signs (When to Call 911):</h3>
        <ul style="padding-left: 20px; font-size: 13px;">
          ${avs.emergency_danger_signs.map(s => `<li>${escapeHTML(s)}</li>`).join("")}
        </ul>
        <h3 style="font-size: 16px; color: #059669; margin-top: 16px;">💊 Medication Instructions:</h3>
        <ul style="padding-left: 20px; font-size: 13px;">
          ${avs.medications_instructions.map(m => `<li>${escapeHTML(m)}</li>`).join("")}
        </ul>
        <div style="margin-top: 20px; padding: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; color: #64748b;">
          Triage Verification Code: <strong>${escapeHTML(avs.telehealth_verification_code)}</strong> | Encounter ID: <strong>${escapeHTML(avs.encounter_id)}</strong>
        </div>
      </div>
    `;
    el.chartModalOverlay.classList.add("active");

  } catch (err) {
    console.error("AVS generation error:", err);
  }
}

function openPrintableChartModal() {
  if (state.sendingEncounter === state.encounterId || state.extractingEncounter === state.encounterId) { showNotice("Finish the current update before opening the chart."); return; }
  if (!state.latestAssessment) {
    showNotice("Please conduct a clinical intake or load a scenario first.");
    return;
  }

  const p = state.patientProfile;
  const a = state.latestAssessment;

  el.printableChartBody.innerHTML = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.5; padding: 10px;">
      <div style="border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
          <h1 style="font-size: 22px; margin: 0 0 4px 0; letter-spacing: -0.5px;">Vaani · Encounter summary</h1>
          <div style="font-size: 13px; color: #555;">VAANI CLINICAL TELEMEDICINE & EMERGENCY TRIAGE SERVICE</div>
        </div>
        <div style="text-align: right; font-size: 12px; font-family: monospace;">
          <strong>ENCOUNTER ID:</strong> ${state.encounterId}<br>
          <strong>DATE/TIME:</strong> ${new Date().toUTCString()}
        </div>
      </div>

      <div style="background: #f8fafc; border: 1px solid #cbd5e1; padding: 12px; border-radius: 4px; margin-bottom: 16px; display: grid; grid-template-columns: 2fr 1fr 1fr;">
        <div><strong>Patient Name:</strong> ${escapeHTML(p.name)} | <strong>MRN:</strong> ${escapeHTML(p.mrn)}</div>
        <div><strong>Age / Sex:</strong> ${p.age || 'Unspecified'} / ${escapeHTML(p.biological_sex.toUpperCase())}</div>
        <div><strong>Triage Rating:</strong> <span style="background: #000; color: var(--text-primary); padding: 2px 6px; font-size: 11px; font-weight: bold;">${a.triage_status}</span></div>
      </div>

      <div style="margin-bottom: 14px;">
        <h3 style="font-size: 14px; margin: 0 0 6px 0; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px;">HISTORY OF PRESENT ILLNESS (OLD CARTS)</h3>
        <p style="font-size: 13px; margin: 0 0 6px 0;"><strong>Chief Complaint:</strong> ${escapeHTML(a.chief_complaint)}</p>
        <p style="font-size: 13px; margin: 0 0 6px 0;">
          Onset: ${escapeHTML(a.hpi.onset || 'Unspecified')} | Location: ${escapeHTML(a.hpi.location || 'Unspecified')} | Duration: ${escapeHTML(a.hpi.duration || 'Unspecified')}<br>
          Character: ${escapeHTML(a.hpi.character || 'Unspecified')} | Radiation: ${escapeHTML(a.hpi.radiation || 'None')} | Pain Score: ${a.hpi.severity ?? '--'}/10
        </p>
      </div>

      <div style="margin-bottom: 14px;">
        <h3 style="font-size: 14px; margin: 0 0 6px 0; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px;">DIAGNOSTIC ASSESSMENT & ICD-10-CM</h3>
        <p style="font-size: 13px; margin: 0 0 6px 0;">
          <strong>Primary Working Diagnosis:</strong> ${escapeHTML(a.differentials[0] ? a.differentials[0].condition_name : 'Acute Symptom Complex')}
          (ICD-10: <code>${escapeHTML(a.differentials[0] ? a.differentials[0].icd10_code : 'R69')}</code>)
        </p>
      </div>

      <div style="margin-bottom: 14px;">
        <h3 style="font-size: 14px; margin: 0 0 6px 0; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px;">RECOMMENDED PLAN & DISPOSITION</h3>
        <p style="font-size: 13px; margin: 0 0 6px 0;"><strong>Disposition:</strong> ${escapeHTML(a.recommended_disposition)}</p>
      </div>

      <div style="border-top: 1px dashed #999; padding-top: 10px; font-size: 11px; color: #666; display: flex; justify-content: space-between;">
        <span>Educational simulation · Review all generated content</span>
        <span>FHIR R4 export preview</span>
      </div>
    </div>
  `;

  el.chartModalOverlay.classList.add("active");
}


// --- HL7 FHIR RELEASE 4 COMPILATION ---
async function compileFHIRBundle() {
  if (state.sendingEncounter === state.encounterId || state.extractingEncounter === state.encounterId) { showNotice("Finish the current update before generating a document."); return; }
  const requestEncounter = state.encounterId;
  const requestRevision = state.revision;
  if (!state.latestAssessment) return;

  try {
    const payload = {
      encounter_id: state.encounterId,
      patient_profile: state.patientProfile,
      assessment: state.latestAssessment,
      biomarkers: state.extractedBiomarkers,
      soap_note: state.lastSoapNote
    };

    const res = await apiFetch("/api/triage/fhir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("FHIR compilation failed");
    const bundle = await res.json();
    if (state.encounterId !== requestEncounter || state.revision !== requestRevision) return;
    state.lastFhirBundle = bundle;

    el.fhirCodeView.textContent = JSON.stringify(bundle.raw_fhir_json, null, 2);
    window.refreshEncounterUI?.();

  } catch (err) {
    console.error("FHIR error:", err);
  }
}


// --- PRESET SCENARIO LOADER ---
async function loadPresetScenarios() {
  try {
    const res = await apiFetch("/api/scenarios");
    if (!res.ok) throw new Error("Could not fetch scenarios");
    const scenarios = await res.json();

    if (!el.scenariosGrid) return;
    el.scenariosGrid.innerHTML = "";

    scenarios.forEach(sc => {
      const card = document.createElement("div");
      card.className = "case-card";
      card.innerHTML = `
        <div class="case-card-head">
          <span class="case-specialty-badge">${sc.specialty}</span>
          <span class="esi-tag esi-${sc.esi_level}" style="font-size: 11px; padding: 2px 8px;">ESI-${sc.esi_level}</span>
        </div>
        <div class="case-card-title">${sc.title}</div>
        <div class="case-card-desc">${sc.chief_complaint}</div>
        <div style="font-size: 11px; color: var(--text-dim); font-family: var(--font-code);">
          Patient: ${sc.patient_profile.name} (${sc.patient_profile.age} yo ${sc.patient_profile.biological_sex})
        </div>
        <button class="btn-action" style="margin-top: 8px; justify-content: center; color: var(--clinical-cyan); border-color: rgba(0, 229, 255, 0.3);">
          ▶ LOAD & EXECUTE CASE
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
  resetEncounter(sc.patient_profile);
  const scenarioEncounter = state.encounterId;

  if (sc.id === "scenario-stemi-cardiac") {
    document.querySelector('[data-rhythm="STEMI"]').click();
  } else if (sc.id === "scenario-asthma-bronchospasm") {
    document.querySelector('[data-rhythm="TACHY"]').click();
  } else if (sc.id === "scenario-stroke-fast") {
    document.querySelector('[data-rhythm="NSR"]').click();
  }

  el.dialogueStream.innerHTML = `
    <div class="message-bubble-row agent">
      <div class="bubble-meta">Vaani · Intake assistant • INTAKE</div>
      <div class="bubble-text">
        Welcome to Vaani. This is a simulated clinical intake.
        Please describe what symptoms or medical emergency you are experiencing today.
      </div>
    </div>
  `;

  document.querySelector('[data-target="suite-telephony"]').click();

  for (const msg of sc.sample_dialogue) {
    if (state.encounterId !== scenarioEncounter) return;
    if (!await sendPatientMessage(msg.content)) return;
    await new Promise(r => setTimeout(r, 240));
  }

  if (state.encounterId !== scenarioEncounter) return;
  if (sc.lab_text_snippet) {
    el.labInputText.value = sc.lab_text_snippet;
    await extractBiomarkersFromText(sc.lab_text_snippet);
  }

  if (state.encounterId === scenarioEncounter) await generateSOAPNote();
}
