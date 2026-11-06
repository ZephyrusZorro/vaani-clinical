"""
Vaani Clinical (वाणी) — Patient After-Visit Summary (AVS) Generator
Transforms high-density clinical documentation into clear, compassionate, 6th-grade reading level
patient-facing discharge and telephone triage instructions.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from backend.models import PatientProfile, TriageAssessment, SOAPNote


class AfterVisitSummary(BaseModel):
    encounter_id: str
    patient_name: str
    mrn: str
    created_at: str
    triage_acuity_level: str
    plain_language_diagnosis: str
    what_happened_today: str
    medications_instructions: List[str]
    emergency_danger_signs: List[str]
    next_steps_and_follow_up: str
    telehealth_verification_code: str
    formatted_document_markdown: str


class AVSGenerator:
    """Produces empathetic, patient-friendly medical encounter summaries."""

    def generate_avs(
        self,
        encounter_id: str,
        patient: PatientProfile,
        assessment: TriageAssessment,
        soap_note: Optional[SOAPNote] = None
    ) -> AfterVisitSummary:
        now_str = datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")
        verif_code = f"VAANI-{encounter_id[-6:].upper()}"

        # Plain language diagnosis mapping
        primary = assessment.differentials[0].condition_name if assessment.differentials else "Health Evaluation"
        plain_diag = self._to_plain_language(primary)

        # What happened summary
        what_happened = (
            f"You spoke with the Vaani Clinical Triage Service regarding {assessment.chief_complaint.lower()}. "
            f"Our clinical evaluation flagged this visit as **{assessment.triage_status}**. "
            f"Your symptoms were carefully documented for your care team."
        )

        # Medication instructions
        med_instructions = []
        if assessment.esi_level <= 2:
            med_instructions.append("⚠️ DO NOT delay emergency medical care to take home medications unless specifically told by a paramedic.")
            if "RF-CARDIAC-STEMI" in [rf.alert_code for rf in assessment.red_flags]:
                med_instructions.append("If instructed by emergency medical dispatch: Chew one 325 mg adult aspirin tablet with water (do not take if you have an active bleeding ulcer or true aspirin allergy).")
        else:
            med_instructions.append("Continue your regular daily prescription medications as directed by your primary doctor.")
            med_instructions.append("Stay well hydrated by sipping water, clear broths, or electrolyte solutions.")

        # Danger signs
        danger_signs = [
            "Sudden crushing, squeezing, or tight chest pain that spreads to your arm, neck, or jaw",
            "Sudden numbness or weakness in your face, arm, or leg (especially on one side of your body)",
            "Sudden difficulty speaking, garbled words, or trouble understanding speech",
            "Severe shortness of breath, loud wheezing, or feeling like you cannot breathe",
            "Fainting, passing out, or sudden severe dizziness",
            "Coughing up blood or sudden uncontrollable bleeding"
        ]

        # Next steps
        if assessment.esi_level <= 2:
            next_steps = (
                "**URGENT ACTION NEEDED:** Please proceed immediately to the nearest Emergency Department "
                "or call Emergency Medical Services (911). Bring your photo ID, medication list, and this summary with you. "
                "Do not attempt to drive yourself."
            )
        elif assessment.esi_level == 3:
            next_steps = (
                "Please schedule an in-person appointment at an Urgent Care clinic or with your doctor within the next 24 hours. "
                "Rest, stay hydrated, and monitor your symptoms closely."
            )
        else:
            next_steps = (
                "Rest at home and take supportive over-the-counter measures as needed. "
                "If your symptoms do not improve within 48 to 72 hours, contact your primary care clinic."
            )

        # Markdown Document
        doc_md = f"""# PATIENT AFTER-VISIT SUMMARY & INSTRUCTIONS
**Patient Name:** {patient.name} | **MRN:** `{patient.mrn}`  
**Encounter Date:** {now_str} | **Triage Case Code:** `{verif_code}`

---

### 🩺 What We Evaluated Today
**Condition:** **{plain_diag}** ({primary})  
**Triage Category:** **{assessment.triage_status}**

{what_happened}

---

### 🚨 When to Call 911 Immediately (Danger Signs)
If you experience any of the following warning signs, call 911 or have someone drive you to the nearest Emergency Room right away:
{chr(10).join([f"- ⚠️ {sign}" for sign in danger_signs])}

---

### 💊 Medication Guidance
{chr(10).join([f"- {med}" for med in med_instructions])}

---

### 📅 What to Do Next
{next_steps}

---
*For hospital triage staff: This patient encounter was processed by the Vaani Clinical Decision Support System. Reference encounter code `{encounter_id}` for HL7 FHIR v4 transaction bundle details.*
"""

        return AfterVisitSummary(
            encounter_id=encounter_id,
            patient_name=patient.name,
            mrn=patient.mrn,
            created_at=now_str,
            triage_acuity_level=assessment.triage_status,
            plain_language_diagnosis=plain_diag,
            what_happened_today=what_happened,
            medications_instructions=med_instructions,
            emergency_danger_signs=danger_signs,
            next_steps_and_follow_up=next_steps,
            telehealth_verification_code=verif_code,
            formatted_document_markdown=doc_md
        )

    def _to_plain_language(self, medical_term: str) -> str:
        term_lower = medical_term.lower()
        if "myocardial infarction" in term_lower or "coronary" in term_lower:
            return "Suspected Heart Attack / Acute Heart Concern"
        elif "ischemic" in term_lower or "stroke" in term_lower or "cerebral" in term_lower:
            return "Suspected Stroke / Acute Brain Blood Flow Interruption"
        elif "ketoacidosis" in term_lower or "dka" in term_lower:
            return "Severely High Blood Sugar with Acid Buildup (Diabetic Emergency)"
        elif "anaphylaxis" in term_lower:
            return "Severe Allergic Reaction (Airway Emergency)"
        elif "asthma" in term_lower or "bronchospasm" in term_lower:
            return "Acute Asthma Flare-Up / Breathing Difficulty"
        elif "respiratory" in term_lower or "rhinovirus" in term_lower:
            return "Upper Respiratory Illness / Common Cold Symptoms"
        elif "gastroenteritis" in term_lower:
            return "Stomach Flu / Gastrointestinal Upset"
        return medical_term
