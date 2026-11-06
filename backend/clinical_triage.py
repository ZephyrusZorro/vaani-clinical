"""
Vaani Clinical (वाणी) — Clinical Triage & Telephony Reasoning Engine
Implements:
1. Conversational State Machine (INTAKE -> HPI_INVESTIGATION -> MEDS_ALLERGIES -> ASSESSMENT -> DISPOSITION)
2. Semantic OLD CARTS Parameter Extraction (Onset, Location, Duration, Character, Aggravating, Relieving, Radiation, Timing, Severity)
3. Emergency Red-Flag Detection (STEMI, Acute Stroke FAST, Anaphylaxis, Sepsis, DKA, PE, Tension Pneumothorax)
4. Emergency Severity Index (ESI Levels 1 to 5) Scoring
5. Differential Diagnosis Generator with ICD-10 diagnostic codes
6. Clinical Telephony Agent Response Generator with TTS-optimized speech output
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from backend.models import (
    PatientProfile,
    ClinicalMessage,
    OLDCARTSParameters,
    RedFlagAlert,
    DifferentialDiagnosis,
    TriageAssessment,
    BiomarkerRecord
)


# --- Red-Flag Rule Definitions ---
RED_FLAG_RULES = [
    {
        "alert_code": "RF-CARDIAC-STEMI",
        "severity": "CRITICAL_EMERGENCY",
        "patterns": [
            r"\b(crushing|heavy|elephant|tight|pressure)\b.*?\b(chest|breastbone|sternum)\b",
            r"\b(radiat(ing|es)|traveling|spread(s|ing)?)\b.*?\b(left arm|jaw|neck|back|shoulder)\b",
            r"\bchest pain\b.*?\b(sweat(ing|y)?|diaphoresis|short(ness)? of breath|nausea)\b",
            r"\bsudden severe chest pain\b"
        ],
        "risk": "Acute Coronary Syndrome / Suspected ST-Elevation Myocardial Infarction (STEMI)",
        "immediate_action": "Activate Emergency Medical Services (911/108/999). Direct patient to sit, chew 325 mg non-enteric aspirin if no contraindications, unlock entrance door.",
        "esi": 1,
        "differentials": [
            DifferentialDiagnosis(
                condition_name="Acute Myocardial Infarction",
                icd10_code="I21.9",
                probability="High",
                justification="Substernal crushing chest pain with classic radiation and autonomic symptoms."
            ),
            DifferentialDiagnosis(
                condition_name="Unstable Angina Pectoris",
                icd10_code="I20.0",
                probability="Moderate",
                justification="Ischemic cardiac symptoms occurring at rest or escalating in severity."
            ),
            DifferentialDiagnosis(
                condition_name="Acute Aortic Dissection",
                icd10_code="I71.00",
                probability="Consider",
                justification="Must rule out if tearing pain radiates through to the interscapular region."
            )
        ]
    },
    {
        "alert_code": "RF-NEURO-FAST-STROKE",
        "severity": "CRITICAL_EMERGENCY",
        "patterns": [
            r"\b(facial|face)\b.*?\b(droop|drooping|slump|numbness|paralysis)\b",
            r"\b(droop|drooping|slump|numbness|paralysis)\b.*?\b(facial|face)\b",
            r"\b(arm|leg|one side|hemiparesis)\b.*?\b(weakness|numbness|drift|cannot raise|can't lift|dead weight)\b",
            r"\b(cannot raise|can't lift|weakness|numbness|drift)\b.*?\b(arm|leg)\b",
            r"\b(slurred|slur|incoherent|cannot speak|garbled)\b.*?\b(speech|words|talk)\b",
            r"\b(speech|words|talk)\b.*?\b(slurred|slur|incoherent|cannot speak|garbled)\b",
            r"\bsudden severe headache\b.*?\b(worst of my life|thunderclap)\b",
            r"\b(loss of vision|diplopia|double vision)\b.*?\bsudden\b"
        ],
        "risk": "Acute Ischemic or Hemorrhagic Stroke / Cerebrovascular Accident (CVA)",
        "immediate_action": "Immediate acute stroke alert protocol. Note exact 'Last Known Well' time. Do NOT administer aspirin until non-contrast head CT rules out intracranial hemorrhage.",
        "esi": 1,
        "differentials": [
            DifferentialDiagnosis(
                condition_name="Acute Ischemic Cerebral Infarction",
                icd10_code="I63.9",
                probability="High",
                justification="Focal neurological deficit matching FAST stroke diagnostic screening."
            ),
            DifferentialDiagnosis(
                condition_name="Transient Ischemic Attack (TIA)",
                icd10_code="G45.9",
                probability="Moderate",
                justification="Temporary neurological disruption with potential pending full infarction."
            ),
            DifferentialDiagnosis(
                condition_name="Subarachnoid Hemorrhage",
                icd10_code="I60.9",
                probability="Consider",
                justification="Sudden maximal intensity thunderclap cephalalgia with focal deficits."
            )
        ]
    },
    {
        "alert_code": "RF-ANAPHYLAXIS",
        "severity": "CRITICAL_EMERGENCY",
        "patterns": [
            r"\b(swollen|swelling|swell|tight|closing)\b.*?\b(tongue|lip|throat|uvula|airway)\b",
            r"\b(tongue|lip|throat|uvula|airway)\b.*?\b(swollen|swelling|swell|tight|closing)\b",
            r"\b(wheezing|stridor|choking|gasping|cannot breathe)\b.*?\b(hive|rash|urticaria|sting|peanut|seafood)\b",
            r"\b(hive|rash|urticaria|sting|peanut|seafood)\b.*?\b(wheezing|stridor|choking|gasping|cannot breathe)\b",
            r"\bhives\b.*?\b(throat tight|dizzy|passed out|syncope)\b"
        ],
        "risk": "Anaphylaxis / Severe Airway Compromise with Impending Respiratory Arrest",
        "immediate_action": "Immediate Intramuscular Epinephrine 0.3-0.5 mg (1:1000) into lateral thigh. Call EMS immediately. Lay patient flat with legs elevated unless respiratory distress is primary.",
        "esi": 1,
        "differentials": [
            DifferentialDiagnosis(
                condition_name="Anaphylactic Reaction",
                icd10_code="T78.2XXA",
                probability="High",
                justification="Multi-organ systemic hypersensitivity response involving cutaneous and airway systems."
            ),
            DifferentialDiagnosis(
                condition_name="Angioedema",
                icd10_code="T78.3XXA",
                probability="Moderate",
                justification="Non-pruritic sub-dermal or mucous membrane swelling involving oral cavity."
            )
        ]
    },
    {
        "alert_code": "RF-METABOLIC-DKA",
        "severity": "URGENT",
        "patterns": [
            r"\b(fruity|sweet|acetone)\s*(breath|smell)\b",
            r"\b(sugar|glucose|blood sugar)\b.*?\b(over 300|over 400|over 500|400|500|600|hi)\b",
            r"\b(vomiting|nausea|abdominal pain)\b.*?\b(type 1|diabetic|high sugar|insulin)\b",
            r"\b(excessive thirst|drinking gallons|constant urination)\b.*?\b(diabetic|glucose)\b"
        ],
        "risk": "Diabetic Ketoacidosis (DKA) / Hyperosmolar Hyperglycemic State (HHS)",
        "immediate_action": "Urgent Emergency Department transport for intravenous fluid resuscitation, electrolyte repletion (Potassium monitoring), and weight-based IV regular insulin infusion.",
        "esi": 2,
        "differentials": [
            DifferentialDiagnosis(
                condition_name="Type 1 Diabetes with Ketoacidosis",
                icd10_code="E10.10",
                probability="High",
                justification="Marked hyperglycemia with metabolic acidosis triggers and osmotic diuresis."
            ),
            DifferentialDiagnosis(
                condition_name="Hyperosmolar Hyperglycemic State",
                icd10_code="E11.00",
                probability="Moderate",
                justification="Severe hyperglycemia without pronounced ketonemia in vulnerable diabetic patients."
            )
        ]
    },
    {
        "alert_code": "RF-RESP-PNEUMOTHORAX-PE",
        "severity": "URGENT",
        "patterns": [
            r"\b(sharp|stabbing)\s*chest pain\b.*?\b(deep breath|inhale|cough)\b",
            r"\bcoughing up blood\b|\bhemoptysis\b",
            r"\bsudden short(ness)? of breath\b.*?\b(swollen calf|swollen leg|after flight|surgery|clot)\b",
            r"\bcan't get enough air\b.*?\b(blue lips|cyanosis)\b"
        ],
        "risk": "Pulmonary Embolism (PE) or Spontaneous Pneumothorax",
        "immediate_action": "Immediate ED triage for CT Pulmonary Angiography (CTPA), D-dimer assay, supplemental oxygen, and hemodynamic stabilization.",
        "esi": 2,
        "differentials": [
            DifferentialDiagnosis(
                condition_name="Pulmonary Embolism",
                icd10_code="I26.99",
                probability="High",
                justification="Sudden dyspnea, pleuritic chest pain, and venous thromboembolic risk factors."
            ),
            DifferentialDiagnosis(
                condition_name="Spontaneous Pneumothorax",
                icd10_code="J93.9",
                probability="Moderate",
                justification="Acute onset pleuritic chest pain with dyspnea."
            )
        ]
    },
    {
        "alert_code": "RF-INFECT-SEPSIS",
        "severity": "URGENT",
        "patterns": [
            r"\b(shaking chills|rigors|high fever)\b.*?\b(confusion|disoriented|lethargic|mottled)\b",
            r"\bfever\b.*?\b(stiff neck|photophobia|cannot touch chin to chest)\b",
            r"\bheart racing\b.*?\b(fever|burning urination|flank pain|hypotension|low bp)\b"
        ],
        "risk": "Systemic Sepsis / Meningeal Infection / Severe Pyelonephritis",
        "immediate_action": "Expedited sepsis pathway: blood cultures x2 prior to broad-spectrum IV antibiotics, serum lactate measurement, and 30 mL/kg crystalloid bolus.",
        "esi": 2,
        "differentials": [
            DifferentialDiagnosis(
                condition_name="Sepsis, Unspecified Organism",
                icd10_code="A41.9",
                probability="High",
                justification="Fever with systemic dysregulation, tachycardia, and altered mentation."
            ),
            DifferentialDiagnosis(
                condition_name="Acute Bacterial Meningitis",
                icd10_code="G00.9",
                probability="Moderate",
                justification="Triad of pyrexia, altered sensorium, and nuchal rigidity."
            )
        ]
    }
]


# --- OLD CARTS Extraction Engine ---
class OLDCARTSExtractor:
    """Extracts HPI dimensions from clinical text."""

    @staticmethod
    def extract_onset(text: str) -> Optional[str]:
        patterns = [
            r"\b(?:started|began|onset|happened|felt it)\s+(?:about\s+)?([0-9]+\s+(?:minutes?|hours?|days?|weeks?|months?)\s+ago)",
            r"\b(?:since|for)\s+([0-9]+\s+(?:minutes?|hours?|days?|weeks?|months?))",
            r"\b(yesterday|this morning|last night|earlier today|suddenly|gradually)\b"
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.groups() else match.group(0).strip()
        return None

    @staticmethod
    def extract_location(text: str) -> Optional[str]:
        locations = [
            ("substernal chest", r"\b(substernal|center of (?:my )?chest|middle of chest)\b"),
            ("left chest", r"\b(left(?:-side)? chest|left breast)\b"),
            ("chest", r"\bchest\b"),
            ("left arm", r"\bleft arm\b"),
            ("head / temple", r"\b(head|temple|forehead|back of head|occipital)\b"),
            ("abdomen / stomach", r"\b(abdomen|stomach|belly|epigastric|flank)\b"),
            ("lower back", r"\b(lower back|lumbar|back)\b"),
            ("throat / airway", r"\b(throat|neck|pharynx|airway)\b"),
            ("calf / leg", r"\b(calf|lower leg|thigh|knee|foot)\b")
        ]
        for label, pattern in locations:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    @staticmethod
    def extract_duration(text: str) -> Optional[str]:
        patterns = [
            (r"\b(constant|continuous|non-stop|unremitting)\b", "Constant / Persistent"),
            (r"\b(intermittent|comes and goes|waxing and waning|in waves)\b", "Intermittent / Waxing and Waning"),
            (r"\b(brief|a few seconds|fleeting)\b", "Brief / Transient"),
            (r"\b(all day|for hours|persisting)\b", "Protracted / Multi-hour")
        ]
        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    @staticmethod
    def extract_character(text: str) -> Optional[str]:
        characters = [
            (r"\b(crushing|heavy|elephant on my chest|vice-like|tight squeeze)\b", "Crushing / Vice-like Pressure"),
            (r"\b(sharp|stabbing|knife-like|lancinating|pleuritic)\b", "Sharp / Stabbing"),
            (r"\b(burning|acidic|heartburn|scorching)\b", "Burning / Pyrosis"),
            (r"\b(throbbing|pulsating|pounding)\b", "Throbbing / Pulsatile"),
            (r"\b(dull|achy|aching|heavy)\b", "Dull Ache"),
            (r"\b(cramping|colicky|spasming)\b", "Cramping / Colicky")
        ]
        for pattern, label in characters:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    @staticmethod
    def extract_aggravating(text: str) -> Optional[str]:
        patterns = [
            (r"\b(worse with|aggravated by|hurts when I)\s+(exert|walk|climb stairs|exercise|breathe|cough|eat|lie down|move)\b", "Exertion / Respiration / Position"),
            (r"\b(exertion|walking|exercise|physical activity)\b", "Physical Exertion"),
            (r"\b(deep breath|breathing in|inspiration|coughing)\b", "Deep Respiration / Inspiration"),
            (r"\b(eating|spicy food|meals|lying flat|recumbent)\b", "Postprandial / Lying Flat")
        ]
        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    @staticmethod
    def extract_relieving(text: str) -> Optional[str]:
        patterns = [
            (r"\b(better with|relieved by|helps when I)\s+(rest|sit|stop|nitroglycerin|aspirin|antacid|inhaler|water)\b", "Rest / Medication / Position"),
            (r"\b(rest|stopping|sitting down)\b", "Rest / Inactivity"),
            (r"\b(nitroglycerin|nitro|sublingual)\b", "Sublingual Nitroglycerin"),
            (r"\b(antacids?|tums|pepto|pantoprazole)\b", "Antacids / GI Protectants"),
            (r"\b(albuterol|inhaler|nebulizer|puff)\b", "Beta-2 Agonist Inhaler")
        ]
        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    @staticmethod
    def extract_radiation(text: str) -> Optional[str]:
        patterns = [
            (r"\b(radiat(?:es|ing)?|travel(?:s|ing)?|spread(?:s|ing)?)\s+(?:to|down|into)\s+(?:the\s+|my\s+|one's\s+)?(left arm|arm|jaw|neck|back|scapula|teeth|shoulder)\b", "Left Arm / Jaw / Shoulder"),
            (r"\b(shoots?|radiates?)\s+down\s+(?:the\s+|my\s+)?(leg|sciatica)\b", "Lower Extremity"),
            (r"\b(through to the back|interscapular)\b", "Interscapular / Back")
        ]
        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    @staticmethod
    def extract_timing(text: str) -> Optional[str]:
        patterns = [
            (r"\b(morning|waking up|dawn)\b", "Early Morning"),
            (r"\b(night|nocturnal|sleep|woke me up)\b", "Nocturnal Awakening"),
            (r"\b(after meals|postprandial|eating)\b", "Postprandial"),
            (r"\b(gradual onset|progressive)\b", "Progressive")
        ]
        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    @staticmethod
    def extract_severity(text: str) -> Optional[int]:
        # Match "8/10", "8 out of 10", "severity 7", "pain is a 9"
        p = r"\b(?:severity|pain(?:\s+is)?|rated?(?:\s+at)?)?\s*([0-9]|10)\s*(?:/|\s*out of\s*)10\b"
        match = re.search(p, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Match standalone "pain is 8", "pain is an 8"
        p2 = r"\bpain\s+(?:is\s+(?:a|an\s+)?)?([1-9]|10)\b"
        match2 = re.search(p2, text, re.IGNORECASE)
        if match2:
            return int(match2.group(1))

        # Qualitative mapping if no number
        if re.search(r"\b(unbearable|excruciating|worst pain|10/10)\b", text, re.IGNORECASE):
            return 10
        elif re.search(r"\b(severe|intense|very bad|terrible)\b", text, re.IGNORECASE):
            return 8
        elif re.search(r"\b(moderate|bothersome|uncomfortable)\b", text, re.IGNORECASE):
            return 5
        elif re.search(r"\b(mild|slight|minor)\b", text, re.IGNORECASE):
            return 2
        return None


# --- Clinical Triage Engine ---
class ClinicalTriageEngine:
    """Core intelligent reasoning engine for clinical telephony triage."""

    def __init__(self):
        self.oldcarts_extractor = OLDCARTSExtractor()

    def update_oldcarts(self, current: OLDCARTSParameters, message: str) -> OLDCARTSParameters:
        """Merge newly detected OLD CARTS attributes from incoming message."""
        updated = current.model_copy()

        onset = self.oldcarts_extractor.extract_onset(message)
        if onset and not updated.onset:
            updated.onset = onset

        loc = self.oldcarts_extractor.extract_location(message)
        if loc and not updated.location:
            updated.location = loc

        dur = self.oldcarts_extractor.extract_duration(message)
        if dur and not updated.duration:
            updated.duration = dur

        char = self.oldcarts_extractor.extract_character(message)
        if char and not updated.character:
            updated.character = char

        agg = self.oldcarts_extractor.extract_aggravating(message)
        if agg and not updated.aggravating:
            updated.aggravating = agg

        rel = self.oldcarts_extractor.extract_relieving(message)
        if rel and not updated.relieving:
            updated.relieving = rel

        rad = self.oldcarts_extractor.extract_radiation(message)
        if rad and not updated.radiation:
            updated.radiation = rad

        timing = self.oldcarts_extractor.extract_timing(message)
        if timing and not updated.timing:
            updated.timing = timing

        sev = self.oldcarts_extractor.extract_severity(message)
        if sev is not None:
            updated.severity = sev

        return updated

    def evaluate_red_flags(self, full_dialogue_text: str) -> Tuple[List[RedFlagAlert], int, List[DifferentialDiagnosis]]:
        """Scans dialog for clinical emergency red flags and assigns ESI triage level."""
        active_alerts: List[RedFlagAlert] = []
        differentials: List[DifferentialDiagnosis] = []
        min_esi = 5

        for rule in RED_FLAG_RULES:
            triggered = False
            for pat in rule["patterns"]:
                if re.search(pat, full_dialogue_text, re.IGNORECASE):
                    triggered = True
                    break

            if triggered:
                alert = RedFlagAlert(
                    alert_code=rule["alert_code"],
                    severity=rule["severity"],
                    symptom_trigger=rule["risk"],
                    clinical_risk=rule["risk"],
                    immediate_action=rule["immediate_action"]
                )
                active_alerts.append(alert)
                differentials.extend(rule["differentials"])
                if rule["esi"] < min_esi:
                    min_esi = rule["esi"]

        # If no severe red flag triggered, evaluate routine / urgent scenarios
        if not active_alerts:
            # Check if presentation is explicitly mild/routine or denies fever
            has_denied_fever = bool(re.search(r"\b(no|denies|without)\s+fever\b", full_dialogue_text, re.IGNORECASE))
            has_fever = bool(re.search(r"\b(fever|chills|high temp)\b", full_dialogue_text, re.IGNORECASE)) and not has_denied_fever
            is_mild = bool(re.search(r"\b(mild|slight|scratchy throat|runny nose|cold|congestion)\b", full_dialogue_text, re.IGNORECASE))

            if is_mild and not has_fever:
                min_esi = 4
                differentials.append(DifferentialDiagnosis(
                    condition_name="Mild Upper Respiratory Tract Symptoms / Rhinovirus",
                    icd10_code="J00",
                    probability="High",
                    justification="Mild localized symptoms without fever, respiratory distress, or systemic toxemia."
                ))
            elif has_fever or re.search(r"\b(chills|temperature|cough|sore throat)\b", full_dialogue_text, re.IGNORECASE):
                min_esi = 3
                differentials.append(DifferentialDiagnosis(
                    condition_name="Upper Respiratory Infection / Viral Syndrome",
                    icd10_code="J06.9",
                    probability="High",
                    justification="Acute febrile illness with pharyngeal and respiratory symptoms."
                ))
            elif re.search(r"\b(vomiting|diarrhea|nausea|food poisoning)\b", full_dialogue_text, re.IGNORECASE):
                min_esi = 3
                differentials.append(DifferentialDiagnosis(
                    condition_name="Acute Gastroenteritis",
                    icd10_code="A09",
                    probability="High",
                    justification="Gastrointestinal symptoms with dehydration risk."
                ))
            elif re.search(r"\b(headache|migraine)\b", full_dialogue_text, re.IGNORECASE):
                min_esi = 4
                differentials.append(DifferentialDiagnosis(
                    condition_name="Migraine without Aura",
                    icd10_code="G43.909",
                    probability="Moderate",
                    justification="Episodic cephalalgia without acute neuro focal red flags."
                ))
            elif re.search(r"\b(rash|itch|eczema|allergy)\b", full_dialogue_text, re.IGNORECASE):
                min_esi = 4
                differentials.append(DifferentialDiagnosis(
                    condition_name="Allergic Dermatitis / Urticaria",
                    icd10_code="L50.9",
                    probability="Moderate",
                    justification="Isolated cutaneous pruritic eruption without airway compromise."
                ))
            else:
                min_esi = 5
                differentials.append(DifferentialDiagnosis(
                    condition_name="Routine Health Assessment / Non-urgent",
                    icd10_code="Z00.00",
                    probability="High",
                    justification="Stable presentation requiring routine outpatient follow-up."
                ))

        return active_alerts, min_esi, differentials

    def determine_triage_status(self, esi_level: int) -> str:
        mapping = {
            1: "ESI-1 RESUSCITATION",
            2: "ESI-2 EMERGENT",
            3: "ESI-3 URGENT",
            4: "ESI-4 LESS URGENT",
            5: "ESI-5 ROUTINE"
        }
        return mapping.get(esi_level, "ESI-3 URGENT")

    def generate_agent_reply(
        self,
        patient_message: str,
        dialogue_history: List[ClinicalMessage],
        hpi: OLDCARTSParameters,
        red_flags: List[RedFlagAlert],
        current_phase: str
    ) -> Tuple[str, str, str]:
        """
        Generates clinical telephony response, speech text, and determines next phase.
        Returns: (agent_reply, agent_speech_text, next_phase)
        """
        # Critical Emergency Immediate Intervention
        critical_flags = [rf for rf in red_flags if rf.severity == "CRITICAL_EMERGENCY"]
        if critical_flags:
            top_flag = critical_flags[0]
            reply = (
                f"🚨 **EMERGENCY MEDICAL ADVISORY (CRITICAL)** 🚨\n\n"
                f"Patient safety is our absolute priority. Based on your symptoms (**{top_flag.clinical_risk}**), "
                f"immediate emergency intervention is warranted.\n\n"
                f"**IMMEDIATE DIRECTIVE:** {top_flag.immediate_action}\n\n"
                f"Our clinical protocol has flagged this case for Emergency Medical Services dispatch. "
                f"Please do not drive yourself. Remain seated, breathe steadily, and have someone stand by the door."
            )
            speech = (
                f"Attention: Based on your description of {top_flag.clinical_risk}, you require immediate emergency medical care. "
                f"Please call 911 or your local emergency dispatch immediately. Sit down, do not exert yourself, and unlock your front door. "
                f"A clinician is standing by."
            )
            return reply, speech, "DISPOSITION"

        # Urgent Flag
        urgent_flags = [rf for rf in red_flags if rf.severity == "URGENT"]
        if urgent_flags:
            top_flag = urgent_flags[0]
            reply = (
                f"⚠️ **URGENT CLINICAL ALERT** ⚠️\n\n"
                f"Your symptoms reflect an urgent clinical risk (**{top_flag.clinical_risk}**).\n\n"
                f"**Clinical Instruction:** {top_flag.immediate_action}\n\n"
                f"Could you let me know if you take any daily medications or have known drug allergies while I prepare your clinical transfer summary?"
            )
            speech = (
                f"Your symptoms require urgent evaluation at an emergency clinic or hospital. "
                f"Before you depart, please tell me what medications you are taking and if you have any drug allergies."
            )
            return reply, speech, "MEDS_ALLERGIES"

        # Investigating OLD CARTS: find what's missing
        missing_prompts = []
        if not hpi.onset:
            missing_prompts.append(("onset", "Exactly when did this symptom first start? Was it sudden or gradual?"))
        if not hpi.character:
            missing_prompts.append(("character", "How would you describe the sensation? (For example: sharp, crushing, burning, dull, or throbbing?)"))
        if not hpi.radiation and hpi.location and "chest" in hpi.location.lower():
            missing_prompts.append(("radiation", "Does the discomfort radiate or spread anywhere else, such as your left arm, neck, jaw, or shoulder?"))
        if hpi.severity is None:
            missing_prompts.append(("severity", "On a scale from 1 to 10, where 10 is the worst pain imaginable, how would you rate it right now?"))
        if not hpi.aggravating:
            missing_prompts.append(("aggravating", "Does anything make the discomfort noticeably worse, like taking a deep breath, moving, or physical effort?"))

        if missing_prompts and current_phase in ("INTAKE", "HPI_INVESTIGATION"):
            # Ask the top 1 or 2 missing clinical questions
            chosen = missing_prompts[:2]
            q_text = " ".join([q[1] for q in chosen])
            reply = (
                f"Thank you for sharing that with me. I am recording these details into your clinical intake chart.\n\n"
                f"To help our medical team assess your situation accurately:\n"
                f"{''.join([f'- {q[1]}\n' for q in chosen])}"
            )
            speech = f"I understand. To help us assess this accurately, {q_text}"
            return reply, speech, "HPI_INVESTIGATION"

        # If OLD CARTS is well explored, ask about Meds and Allergies
        if current_phase == "HPI_INVESTIGATION":
            reply = (
                f"Thank you. We have recorded your history of present illness.\n\n"
                f"To ensure safe medical recommendations, please list:\n"
                f"1. Any prescription or over-the-counter medications you currently take.\n"
                f"2. Any known drug allergies or adverse reactions (e.g., penicillin, sulfa, aspirin)."
            )
            speech = "We have documented your symptoms. Next, please tell me about any current medications you take, and whether you have any drug allergies."
            return reply, speech, "MEDS_ALLERGIES"

        # If in Meds/Allergies phase, wrap up to assessment
        if current_phase == "MEDS_ALLERGIES":
            reply = (
                f"Thank you. Your medication and allergy history is now cross-referenced in your file.\n\n"
                f"I am synthesizing your comprehensive clinical assessment and triage summary now. "
                f"Please review the differential diagnoses and recommended disposition below."
            )
            speech = "Thank you. Your clinical assessment and triage disposition are now ready for review."
            return reply, speech, "ASSESSMENT"

        # Default disposition phase
        reply = (
            f"Your clinical triage evaluation is complete. A complete SOAP note and HL7 FHIR v4 transaction bundle "
            f"have been generated and can be exported to your health system or electronic health record (EHR)."
        )
        speech = "Your clinical encounter documentation and electronic health record transfer bundle have been synthesized."
        return reply, speech, "DISPOSITION"

    def process_triage(
        self,
        patient_message: str,
        dialogue_history: List[ClinicalMessage],
        current_hpi: Optional[OLDCARTSParameters] = None,
        patient_profile: Optional[PatientProfile] = None
    ) -> Tuple[TriageAssessment, str, str, str, bool]:
        """
        Executes end-to-end triage evaluation over dialogue turn.
        Returns: (TriageAssessment, agent_reply, agent_speech_text, next_phase, has_critical_red_flag)
        """
        hpi = current_hpi or OLDCARTSParameters()
        hpi = self.update_oldcarts(hpi, patient_message)

        # Aggregate dialogue text for red-flag search
        all_text = " ".join([m.content for m in dialogue_history] + [patient_message])

        red_flags, esi_level, differentials = self.evaluate_red_flags(all_text)
        triage_status = self.determine_triage_status(esi_level)

        # Chief complaint determination
        chief_complaint = hpi.location or "Acute symptomatic presentation"
        if not hpi.location and dialogue_history:
            chief_complaint = dialogue_history[0].content[:60] + "..."
        elif not hpi.location:
            chief_complaint = patient_message[:60]

        # Recommended disposition
        if esi_level == 1:
            disp = "IMMEDIATE EMERGENCY RESUSCITATION / EMS 911 PROTOCOL"
        elif esi_level == 2:
            disp = "EMERGENCY DEPARTMENT EVALUATION (ESCALATION WITHIN 15 MINUTES)"
        elif esi_level == 3:
            disp = "URGENT CARE CLINIC OR EXPEDITED OUTPATIENT EVALUATION (< 24 HOURS)"
        elif esi_level == 4:
            disp = "PRIMARY CARE CLINIC APPOINTMENT (WITHIN 2-3 DAYS)"
        else:
            disp = "ROUTINE TELEHEALTH ADVICE / HOME CARE WITH RED-FLAG RETURN PRECAUTIONS"

        assessment = TriageAssessment(
            chief_complaint=chief_complaint,
            hpi=hpi,
            esi_level=esi_level,
            triage_status=triage_status,
            red_flags=red_flags,
            differentials=differentials,
            recommended_disposition=disp
        )

        has_critical = any(rf.severity == "CRITICAL_EMERGENCY" for rf in red_flags)

        # Compute current phase
        if has_critical:
            current_phase = "DISPOSITION"
        elif len(dialogue_history) <= 1 and (not hpi.onset or not hpi.severity):
            current_phase = "HPI_INVESTIGATION"
        elif len(dialogue_history) <= 3 and not (patient_profile and patient_profile.allergies):
            current_phase = "MEDS_ALLERGIES"
        else:
            current_phase = "ASSESSMENT"

        reply, speech, next_phase = self.generate_agent_reply(
            patient_message,
            dialogue_history,
            hpi,
            red_flags,
            current_phase
        )

        return assessment, reply, speech, next_phase, has_critical
