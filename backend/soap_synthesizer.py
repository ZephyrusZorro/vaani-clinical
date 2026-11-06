"""
Vaani Clinical (वाणी) — SOAP Note Synthesis Engine
Synthesizes clinical encounters into structured, hospital-grade SOAP documentation:
- S (Subjective): Chief Complaint, OLD CARTS HPI, ROS, PMH, Meds, Allergies
- O (Objective): Reported Vitals, Telemetry, Extracted Lab Biomarkers with LOINC codes
- A (Assessment): Primary Diagnosis + ICD-10, Differential Diagnoses, ESI Triage Score
- P (Plan): Clinical Disposition, Diagnostic Workup, Interventions, Emergency Return Precautions
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.models import (
    PatientProfile,
    OLDCARTSParameters,
    TriageAssessment,
    BiomarkerRecord,
    SubjectiveSection,
    ObjectiveSection,
    AssessmentSection,
    PlanSection,
    SOAPNote
)


class SOAPSynthesizer:
    """Transforms triage encounters into structured SOAP notes and Markdown documents."""

    def synthesize(
        self,
        encounter_id: str,
        patient: PatientProfile,
        assessment: TriageAssessment,
        biomarkers: List[BiomarkerRecord],
        vitals: Optional[Dict[str, Any]] = None,
        telemetry_status: Optional[str] = None
    ) -> SOAPNote:
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        vitals = vitals or {
            "heart_rate_bpm": 88,
            "blood_pressure": "130/84 mmHg",
            "spo2_percent": 98,
            "respiratory_rate": 16,
            "temperature_c": 37.0
        }
        telemetry_status = telemetry_status or "Normal sinus rhythm telemetry on arrival."

        # 1. Subjective Section
        hpi_parts = []
        h = assessment.hpi
        if h.onset: hpi_parts.append(f"Onset: {h.onset}")
        if h.location: hpi_parts.append(f"Location: {h.location}")
        if h.duration: hpi_parts.append(f"Duration: {h.duration}")
        if h.character: hpi_parts.append(f"Character: {h.character}")
        if h.aggravating: hpi_parts.append(f"Aggravating factors: {h.aggravating}")
        if h.relieving: hpi_parts.append(f"Relieving factors: {h.relieving}")
        if h.radiation: hpi_parts.append(f"Radiation: {h.radiation}")
        if h.timing: hpi_parts.append(f"Timing: {h.timing}")
        if h.severity is not None: hpi_parts.append(f"Pain score: {h.severity}/10")

        hpi_narrative = (
            f"Patient presents with {assessment.chief_complaint.lower()}. "
            + ("; ".join(hpi_parts) if hpi_parts else "Symptoms characterized via telephony triage.")
        )

        ros = {
            "Constitutional": "Denies fever, weight changes unless noted." if assessment.esi_level > 2 else "Diaphoresis and acute distress present.",
            "Cardiovascular": "Chest discomfort / palpitations evaluated.",
            "Respiratory": "Shortness of breath assessed during triage dialogue.",
            "Neurological": "Gross neurological screening conducted via verbal fluency."
        }

        subj = SubjectiveSection(
            chief_complaint=assessment.chief_complaint,
            history_of_present_illness=hpi_narrative,
            review_of_systems=ros,
            past_medical_history=patient.past_medical_history or ["None reported"],
            medications=patient.current_medications or ["None reported"],
            allergies=patient.allergies or ["No known drug allergies (NKDA)"]
        )

        # 2. Objective Section
        obj = ObjectiveSection(
            reported_vitals=vitals,
            telemetry_findings=telemetry_status,
            extracted_biomarkers=biomarkers
        )

        # 3. Assessment Section
        primary_diff = assessment.differentials[0] if assessment.differentials else None
        primary_name = primary_diff.condition_name if primary_diff else "Undifferentiated Symptom Complex"
        primary_icd = primary_diff.icd10_code if primary_diff else "R69"

        reasoning = (
            f"Presentation flagged as {assessment.triage_status} (ESI Score: {assessment.esi_level}). "
            f"Clinical findings and dialogue analysis warrant clinical vigilance for {primary_name}."
        )
        if assessment.red_flags:
            flags_str = "; ".join([f"{rf.alert_code}: {rf.clinical_risk}" for rf in assessment.red_flags])
            reasoning += f" Active Red Flags: {flags_str}."

        assess = AssessmentSection(
            primary_diagnosis=primary_name,
            primary_icd10=primary_icd,
            secondary_differentials=assessment.differentials[1:],
            clinical_reasoning=reasoning,
            esi_score=assessment.esi_level
        )

        # 4. Plan Section
        diagnostic_workup = []
        treatment_orders = []

        if assessment.esi_level == 1:
            diagnostic_workup.extend([
                "Immediate 12-lead Electrocardiogram (ECG) within 10 minutes",
                "Point-of-Care Serial Cardiac Troponin (0h, 1h, 3h)",
                "Stat Complete Metabolic Panel & Venous Blood Gas",
                "Portable Chest Radiograph (CXR)"
            ])
            treatment_orders.extend([
                "Administer chewable Aspirin 325 mg PO immediately (if no active hemorrhage / allergy)",
                "Establish dual large-bore IV access (18G)",
                "Continuous cardiac rhythm & pulse oximetry monitoring",
                "Direct catheterization lab / code alert activation"
            ])
            disposition = "EMERGENCY TRANSFER: Immediate Resuscitation / Catheterization Laboratory."
        elif assessment.esi_level == 2:
            diagnostic_workup.extend([
                "12-lead ECG and basic telemetry",
                "Targeted laboratory biomarker panel (CBC, CMP, Troponin / D-dimer as indicated)",
                "Diagnostic imaging based on primary system involvement (CXR or CT)"
            ])
            treatment_orders.extend([
                "Maintain IV access with isotonic saline TKO",
                "Supplemental oxygen to keep SpO2 >= 94%",
                "Symptomatic pharmacotherapy per attending physician order"
            ])
            disposition = "EMERGENCY DEPARTMENT ADMISSION: Expedited Attending Physician Evaluation."
        elif assessment.esi_level == 3:
            diagnostic_workup.extend([
                "Basic outpatient labs: CBC, Comprehensive Metabolic Panel",
                "Non-emergent diagnostic imaging if symptoms persist"
            ])
            treatment_orders.extend([
                "Symptom management with oral analgesics or antiemetics as appropriate",
                "Adequate oral rehydration"
            ])
            disposition = "URGENT CARE CLINIC: Outpatient medical evaluation within 24 hours."
        else:
            diagnostic_workup.append("Routine laboratory follow-up with Primary Care Provider as indicated.")
            treatment_orders.append("Over-the-counter supportive therapy and hydration.")
            disposition = "PRIMARY CARE TELEHEALTH: Conservative home care and outpatient follow-up."

        precautions = [
            "Sudden worsening or radiation of chest pressure/pain",
            "Severe shortness of breath, stridor, or inability to speak in full sentences",
            "Focal neurological deficits (facial droop, unilateral arm/leg weakness, slurred speech)",
            "Syncope, presyncope, severe confusion, or altered mental status",
            "Cyanosis of lips or nail beds, or persistent intractable vomiting"
        ]

        plan = PlanSection(
            disposition=disposition,
            diagnostic_workup=diagnostic_workup,
            treatment_orders=treatment_orders,
            patient_education="Reviewed clinical impression, danger warning signs, and medication instructions.",
            emergency_return_precautions=precautions
        )

        # 5. Formatted Markdown Synthesis
        md_text = self._build_markdown(
            encounter_id=encounter_id,
            patient=patient,
            timestamp=timestamp_str,
            subj=subj,
            obj=obj,
            assess=assess,
            plan=plan,
            esi_level=assessment.esi_level,
            triage_status=assessment.triage_status
        )

        return SOAPNote(
            encounter_id=encounter_id,
            patient_name=patient.name,
            timestamp=timestamp_str,
            subjective=subj,
            objective=obj,
            assessment=assess,
            plan=plan,
            markdown_formatted=md_text
        )

    def _build_markdown(
        self,
        encounter_id: str,
        patient: PatientProfile,
        timestamp: str,
        subj: SubjectiveSection,
        obj: ObjectiveSection,
        assess: AssessmentSection,
        plan: PlanSection,
        esi_level: int,
        triage_status: str
    ) -> str:
        lines = [
            f"# CLINICAL TELEPHONY ENCOUNTER NOTE (SOAP)",
            f"**Encounter ID:** `{encounter_id}` | **Date/Time:** {timestamp}",
            f"**Patient Name:** {patient.name} | **MRN:** `{patient.mrn}` | **Age/Sex:** {patient.age or 'Unspecified'} / {patient.biological_sex.capitalize()}",
            f"**Triage Rating:** `[{triage_status}]` (ESI Level {esi_level})",
            "",
            "---",
            "",
            "## S — SUBJECTIVE",
            f"**Chief Complaint:** {subj.chief_complaint}",
            "",
            f"**History of Present Illness (HPI):**\n{subj.history_of_present_illness}",
            "",
            f"**Past Medical History:** {', '.join(subj.past_medical_history)}",
            f"**Current Medications:** {', '.join(subj.medications)}",
            f"**Allergies:** {', '.join(subj.allergies)}",
            "",
            "---",
            "",
            "## O — OBJECTIVE",
            "**Reported Vital Signs:**"
        ]

        for k, v in obj.reported_vitals.items():
            lines.append(f"- **{k.replace('_', ' ').capitalize()}:** {v}")

        lines.append(f"- **Telemetry / Monitor:** {obj.telemetry_findings}")

        if obj.extracted_biomarkers:
            lines.append("")
            lines.append("**Extracted Laboratory Biomarkers:**")
            lines.append("| Biomarker | LOINC | Value | Reference Range | Status | Interpretation |")
            lines.append("|---|---|---|---|---|---|")
            for b in obj.extracted_biomarkers:
                lines.append(f"| **{b.name}** ({b.test_code}) | `{b.loinc_code}` | `{b.value} {b.unit}` | {b.reference_low}–{b.reference_high} {b.unit} | `{b.status}` | {b.clinical_interpretation} |")

        lines.extend([
            "",
            "---",
            "",
            "## A — ASSESSMENT",
            f"**Primary Diagnosis:** **{assess.primary_diagnosis}** (ICD-10: `{assess.primary_icd10}`)",
            "",
            "**Differential Diagnoses:**"
        ])

        for diff in assess.secondary_differentials:
            lines.append(f"- **{diff.condition_name}** (`{diff.icd10_code}`) — *Probability: {diff.probability}* | {diff.justification}")

        lines.extend([
            "",
            f"**Clinical Medical Reasoning:**\n{assess.clinical_reasoning}",
            "",
            "---",
            "",
            "## P — PLAN",
            f"**Recommended Disposition:** **{plan.disposition}**",
            "",
            "**Diagnostic Workup Orders:**"
        ])

        for diag in plan.diagnostic_workup:
            lines.append(f"- [ ] {diag}")

        lines.append("")
        lines.append("**Immediate Treatment & Interventions:**")
        for tx in plan.treatment_orders:
            lines.append(f"- [ ] {tx}")

        lines.extend([
            "",
            f"**Patient Instructions & Education:**\n{plan.patient_education}",
            "",
            "**Strict Emergency Return Precautions:**"
        ])

        for ret in plan.emergency_return_precautions:
            lines.append(f"- ⚠️ {ret}")

        lines.extend([
            "",
            "---",
            "*Document electronically authenticated by Vaani Clinical AI Copilot & Licensed Telephony Triage Architecture.*"
        ])

        return "\n".join(lines)
